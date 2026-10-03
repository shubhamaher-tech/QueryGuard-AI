import json
import re
from typing import Dict, Any, List, Optional
from app.llm.schemas import SanitizedPromptContext
from app.privacy import verify_anonymized_or_raise, is_anonymized_safeguard

SYSTEM_PROMPT = """You are QueryGuard AI's Privacy-Safe SQL Optimization Assistant.
Your task is to analyze an anonymized SQL template and propose an equivalent, higher-performance SQL rewrite candidate.

STRICT OPERATIONAL RULES:
1. OUTPUT FORMAT: You must output ONLY a valid JSON object matching the requested schema. Do NOT include markdown code fences (like ```json), commentary, or text outside the JSON object.
2. PRIVACY & TOKENS: You may ONLY use the authorized masked table tokens (TBL_*) and column tokens (COL_*) provided in the user context. Do NOT invent new table or column names.
3. QUERY TYPE: Propose ONLY read-only SELECT queries. Do NOT produce DDL (CREATE, DROP, ALTER) or DML (INSERT, UPDATE, DELETE).
4. SUGGESTED INDEXES: If an index pattern would aid the rewrite, list it strictly inside "suggested_index_patterns" using the authorized tokens.
5. METRICS INTEGRITY: Do not invent cost or latency numbers; the PostgreSQL planner simulator evaluates performance independently.

REQUIRED JSON OUTPUT SCHEMA:
{
  "action_type": "SQL_REWRITE" or "NO_REWRITE",
  "rewritten_sql_template": "string with rewritten SELECT query or null",
  "rewrite_strategy": "short description of the optimization applied",
  "suggested_index_patterns": [
    {
      "table_token": "TBL_...",
      "columns": ["COL_...", "COL_..."],
      "reason": "explanation"
    }
  ],
  "reason_codes": ["string"],
  "assumptions": ["string"],
  "risk_notes": ["string"],
  "expected_benefit_level": "LOW" or "MEDIUM" or "HIGH",
  "confidence": "LOW" or "MEDIUM" or "HIGH"
}
"""

class PromptBuilder:
    """
    Builds strictly sanitized, privacy-safe prompts for local SLM consumption.
    """

    def build_sanitized_context(
        self,
        masked_sql: str,
        fingerprint: str,
        plan_json: Optional[Dict[str, Any]] = None,
        xai_evidence: Optional[Dict[str, Any]] = None,
        bottleneck: str = "Unknown",
        join_count: int = 0,
        plan_depth: int = 1,
    ) -> SanitizedPromptContext:
        # Extract table tokens and column tokens
        table_tokens = list(set(re.findall(r"\bTBL_[A-Z0-9_]+\b", masked_sql)))
        column_tokens = list(set(re.findall(r"\bCOL_[A-Z0-9_]+\b", masked_sql)))

        operators: List[str] = []
        if plan_json:
            root_plan = plan_json.get("Plan", plan_json)
            self._collect_operators(root_plan, operators)

        evidence_signals = []
        if xai_evidence and isinstance(xai_evidence, dict):
            evidence_signals = xai_evidence.get("evidence_signals", [])

        # Assign column type categories from usage
        col_categories = {}
        for col in column_tokens:
            if "date" in col.lower() or "d0" in col.lower() or "d1" in col.lower():
                col_categories[col] = "DATE"
            elif "id" in col.lower() or "r0" in col.lower() or "c0" in col.lower():
                col_categories[col] = "INT"
            else:
                col_categories[col] = "NUM"

        # Table size buckets
        table_size_buckets = {tbl: "LARGE" for tbl in table_tokens}

        return SanitizedPromptContext(
            query_fingerprint=fingerprint,
            query_type="SELECT",
            masked_query_template=masked_sql.strip(),
            join_count=join_count,
            plan_depth=plan_depth,
            bottleneck_labels=[bottleneck],
            sanitized_operator_sequence=operators[:10],
            masked_table_tokens=table_tokens,
            masked_column_tokens=column_tokens,
            column_type_categories=col_categories,
            selectivity_buckets={col: "MEDIUM" for col in column_tokens[:5]},
            table_size_buckets=table_size_buckets,
            existing_masked_index_patterns=[],
            is_partitioned=False,
            baseline_planner_cost_bucket="HIGH",
            rule_reason_codes=[bottleneck.upper().replace(" ", "_")],
            xai_evidence_signals=evidence_signals,
        )

    def format_user_prompt(self, context: SanitizedPromptContext) -> str:
        prompt_data = {
            "query_fingerprint": context.query_fingerprint,
            "masked_query_template": context.masked_query_template,
            "query_type": context.query_type,
            "join_count": context.join_count,
            "plan_depth": context.plan_depth,
            "primary_bottleneck": context.bottleneck_labels,
            "operator_sequence": context.sanitized_operator_sequence,
            "authorized_tables": context.masked_table_tokens,
            "authorized_columns": context.masked_column_tokens,
            "column_types": context.column_type_categories,
            "table_sizes": context.table_size_buckets,
            "xai_signals": context.xai_evidence_signals,
        }

        serialized = json.dumps(prompt_data, indent=2)

        # Enforce in-memory privacy scan: Ensure no plaintext tables, columns, or customer identifiers appear
        for forbidden in ["transactions", "customers", "order_items", "products", "regions", "customer_id", "region_id"]:
            if re.search(rf"\b{re.escape(forbidden)}\b", serialized, re.IGNORECASE):
                raise ValueError(f"Prompt privacy barrier failed: plaintext identifier '{forbidden}' detected in prompt")

        return f"Please analyze this sanitized query and propose an optimized SQL rewrite if beneficial:\n{serialized}"

    def _collect_operators(self, node: Dict[str, Any], ops: List[str]):
        if not isinstance(node, dict):
            return
        op = node.get("Node Type")
        if op:
            ops.append(op)
        for child in node.get("Plans", []):
            self._collect_operators(child, ops)

prompt_builder = PromptBuilder()
