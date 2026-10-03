import hmac
import hashlib
import re
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.llm.schemas import (
    RewriteRouteResult,
    LLMStatusResponse,
    RewriteAnalysisResponse,
)
from app.llm.status_service import llm_status_service

class QueryComplexityRouter:
    """
    Fast heuristic router to determine whether a query requires local SLM
    consultation or should follow the fast rule-based path.
    """

    def __init__(self, hmac_secret: Optional[str] = None):
        self.secret = (hmac_secret or settings.HMAC_TOKEN_SECRET).encode("utf-8")

    def analyze_complexity(
        self,
        masked_sql: str,
        plan_json: Optional[Dict[str, Any]] = None,
        avg_latency_ms: float = 0.0,
        rule_confidence: float = 0.85,
    ) -> RewriteRouteResult:
        reason_codes: List[str] = []
        is_complex = False

        # 1. Join count in masked template
        join_matches = re.findall(r"\bJOIN\b", masked_sql, flags=re.IGNORECASE)
        join_count = len(join_matches)
        if join_count > 2:
            is_complex = True
            reason_codes.append("JOIN_COUNT_EXCEEDED")

        # 2. Correlated or nested subquery check
        subquery_match = re.search(r"\(\s*SELECT\b", masked_sql, flags=re.IGNORECASE)
        if subquery_match:
            is_complex = True
            reason_codes.append("NESTED_OR_CORRELATED_SUBQUERY")

        # 3. Plan tree metrics
        plan_depth = 1
        operators: List[str] = []
        if plan_json:
            root_plan = plan_json.get("Plan", plan_json)
            plan_depth, operators = self._extract_plan_metrics(root_plan)

        if plan_depth > 5:
            is_complex = True
            reason_codes.append("PLAN_DEPTH_EXCEEDED")

        # 4. Historical mean latency > 100 ms
        if avg_latency_ms > 100.0:
            is_complex = True
            reason_codes.append("HIGH_HISTORICAL_LATENCY")

        # 5. Rule engine confidence < 0.70
        if rule_confidence < 0.70:
            is_complex = True
            reason_codes.append("LOW_RULE_ENGINE_CONFIDENCE")

        # 6. Sequential Scan + Nested Loop combination
        has_seq_scan = any("seq" in op.lower() for op in operators)
        has_nested_loop = any("nested" in op.lower() for op in operators)
        if has_seq_scan and has_nested_loop:
            is_complex = True
            reason_codes.append("SEQ_SCAN_AND_NESTED_LOOP_COMBO")

        # 7. Complex aggregate / sort pattern
        has_aggregate = any("aggregate" in op.lower() or "group" in op.lower() for op in operators)
        has_sort = any("sort" in op.lower() for op in operators) or bool(re.search(r"\bORDER\s+BY\b", masked_sql, re.IGNORECASE))
        if has_aggregate and has_sort:
            is_complex = True
            reason_codes.append("COMPLEX_AGGREGATE_SORT_PATTERN")

        # Route decision
        if is_complex:
            route_decision = "COMPLEX_QUERY_SLM_ROUTED"
        else:
            route_decision = "SIMPLE_QUERY_FAST_PATH"
            reason_codes.append("SIMPLE_QUERY_WITHIN_BOUNDS")

        # Compute cache key (HMAC over masked template + features + version)
        cache_key = self._generate_cache_key(masked_sql, plan_depth, operators)

        return RewriteRouteResult(
            is_complex=is_complex,
            route_decision=route_decision,
            route_reason_codes=reason_codes,
            cache_key=cache_key,
        )

    def _extract_plan_metrics(self, node: Dict[str, Any], depth: int = 1) -> tuple[int, List[str]]:
        if not isinstance(node, dict):
            return depth, []

        op = node.get("Node Type", "Unknown")
        ops = [op]
        max_child_depth = depth

        children = node.get("Plans", [])
        for child in children:
            cd, cops = self._extract_plan_metrics(child, depth + 1)
            max_child_depth = max(max_child_depth, cd)
            ops.extend(cops)

        return max_child_depth, ops

    def _generate_cache_key(self, masked_sql: str, plan_depth: int, operators: List[str]) -> str:
        canonical_content = f"{masked_sql.strip()}|depth={plan_depth}|ops={','.join(sorted(set(operators)))}|v1"
        return hmac.new(self.secret, canonical_content.encode("utf-8"), hashlib.sha256).hexdigest()

complexity_router = QueryComplexityRouter()


# ==============================================================================
# FastAPI Router for LLM & SQL Rewrite Endpoints
# ==============================================================================

router = APIRouter(tags=["Local SLM & SQL Rewrite"])

@router.get("/llm/status", response_model=LLMStatusResponse)
def get_llm_status():
    """
    Get local Ollama service and configured SLM readiness status.
    Privacy safe: never exposes secrets, connection strings, or customer data.
    """
    return llm_status_service.get_status()

@router.post("/queries/{query_id}/rewrite/analyze", response_model=RewriteAnalysisResponse)
def analyze_query_rewrite(
    query_id: str,
    force_refresh: bool = Query(False, description="Force re-evaluation bypassing cache"),
    db: Session = Depends(get_db),
):
    """
    Analyze query for SQL rewrite:
    1. Heuristic router checks complexity. Simple queries follow fast rule-based path.
    2. Complex queries consult local SLM with masked/tokenized context only.
    3. AST and SQL safety gateway enforces SELECT-only restrictions.
    4. Evaluates rewrite via PostgreSQL planner EXPLAIN guardrails.
    """
    from app.llm.rewrite_service import sql_rewrite_service
    try:
        return sql_rewrite_service.analyze_query_rewrite(
            db=db,
            query_id=query_id,
            force_refresh=force_refresh,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite analysis failed: {str(e)}")

@router.get("/queries/{query_id}/rewrite", response_model=RewriteAnalysisResponse)
def get_query_rewrite(
    query_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve existing SQL rewrite candidate and evaluation for a query.
    """
    from app.llm.rewrite_service import sql_rewrite_service
    result = sql_rewrite_service.get_query_rewrite(db, query_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"No rewrite analysis found for query '{query_id}'.")
    return result

@router.post("/queries/{query_id}/rewrite/reset-cache")
def reset_query_rewrite_cache(
    query_id: str,
    db: Session = Depends(get_db),
):
    """
    Clear cached rewrite analysis for a specific query.
    """
    from app.llm.rewrite_service import sql_rewrite_service
    sql_rewrite_service.reset_query_rewrite_cache(db, query_id)
    return {
        "status": "success",
        "message": f"Rewrite cache reset for query '{query_id}'.",
        "query_id": query_id,
    }
