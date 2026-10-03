"""
Strict Safety & Privacy Gateway for Interactive Query Analysis Workspace

Enforces:
1. Single-statement SELECT only (no DML, DDL, or administrative commands)
2. Zero SQL comments permitted (anti-obfuscation)
3. Zero multi-statements (no semicolons separating statements)
4. Blacklisted functions (pg_sleep, file access, session mutation)
5. Strict dataset-specific relation allowlists (prevents catalog/system inspection)
6. Resource bounding (max query length, max joins, max AST nesting depth)
"""

import re
from typing import Tuple, Optional, Set, List
import sqlglot
from sqlglot import exp

FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bMERGE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bCOPY\b",
    r"\bCALL\b",
    r"\bDO\b",
    r"\bVACUUM\b",
    r"\bANALYZE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXECUTE\b",
    r"\bSET\b",
    r"\bRESET\b",
    r"\bLOCK\b",
    r"\bLISTEN\b",
    r"\bNOTIFY\b",
]

DANGEROUS_FUNCTIONS = [
    r"\bpg_sleep\b",
    r"\bpg_read_file\b",
    r"\bpg_write_file\b",
    r"\bpg_terminate_backend\b",
    r"\bpg_cancel_backend\b",
    r"\bdblink\b",
    r"\bquery_to_xml\b",
    r"\bversion\b",
    r"\bcurrent_user\b",
    r"\bsystem_user\b",
    r"\bsession_user\b",
    r"\bcurrent_setting\b",
    r"\bset_config\b",
]

# Dataset relation allowlists
DATASET_ALLOWLISTS = {
    "synthetic_ecommerce": {
        "transactions",
        "customers",
        "products",
        "regions",
        "order_items",
    },
    "tpch_sf01": {
        "tpch_region",
        "tpch_nation",
        "tpch_supplier",
        "tpch_part",
        "tpch_partsupp",
        "tpch_customer",
        "tpch_orders",
        "tpch_lineitem",
    },
    "tpch_sf1": {
        "tpch_region",
        "tpch_nation",
        "tpch_supplier",
        "tpch_part",
        "tpch_partsupp",
        "tpch_customer",
        "tpch_orders",
        "tpch_lineitem",
    },
    "job_imdb": {
        "aka_name",
        "aka_title",
        "cast_info",
        "char_name",
        "comp_cast_type",
        "company_name",
        "company_type",
        "complete_cast",
        "info_type",
        "keyword",
        "kind_type",
        "link_type",
        "movie_companies",
        "movie_info",
        "movie_info_idx",
        "movie_keyword",
        "movie_link",
        "name",
        "role_type",
        "title",
    },
}

# Universal allowed tables across all sandbox datasets (or allow all sandbox tables if multi-dataset)
ALL_SANDBOX_TABLES = set()
for tbls in DATASET_ALLOWLISTS.values():
    ALL_SANDBOX_TABLES.update(tbls)

MAX_SQL_LENGTH = 5000
MAX_JOIN_COUNT = 15
MAX_NESTING_DEPTH = 10


class SafetyValidationResult:
    def __init__(self, is_valid: bool, error_code: Optional[str] = None, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_code = error_code
        self.error_message = error_message

    def __bool__(self):
        return self.is_valid


class QuerySafetyValidator:
    """
    Validates user-submitted SQL against strict safety, privacy, and scope invariants.
    """

    @classmethod
    def validate(cls, raw_sql: str, dataset: str = "synthetic_ecommerce") -> SafetyValidationResult:
        if not raw_sql or not raw_sql.strip():
            return SafetyValidationResult(
                is_valid=False,
                error_code="SAFETY_VIOLATION_EMPTY_QUERY",
                error_message="Query input is empty. Please provide a valid SELECT statement.",
            )

        clean_sql = raw_sql.strip()

        # 1. Length check
        if len(clean_sql) > MAX_SQL_LENGTH:
            return SafetyValidationResult(
                is_valid=False,
                error_code="SAFETY_VIOLATION_EXCESSIVE_LENGTH",
                error_message=f"Query length ({len(clean_sql)} chars) exceeds maximum safety limit of {MAX_SQL_LENGTH} chars.",
            )

        # 2. Reject SQL comments (prevents hidden code injections or parser evasion)
        if "--" in clean_sql or "/*" in clean_sql or "*/" in clean_sql:
            return SafetyValidationResult(
                is_valid=False,
                error_code="SAFETY_VIOLATION_COMMENTS_FORBIDDEN",
                error_message="SQL comments ('--' or '/* ... */') are strictly forbidden in QueryGuard analysis queries.",
            )

        # 3. Reject multi-statement (semicolon inside or multiple queries)
        semicolon_stripped = clean_sql.rstrip(";").strip()
        if ";" in semicolon_stripped:
            return SafetyValidationResult(
                is_valid=False,
                error_code="SAFETY_VIOLATION_MULTI_STATEMENT",
                error_message="Multi-statement queries separated by semicolons are strictly forbidden. Submit a single SELECT statement.",
            )

        # 4. Check forbidden keywords (DML, DDL, Session mutation)
        for kw_pattern in FORBIDDEN_KEYWORDS:
            if re.search(kw_pattern, clean_sql, flags=re.IGNORECASE):
                kw_name = kw_pattern.replace(r"\b", "")
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_DML_DETECTED",
                    error_message=f"Forbidden keyword '{kw_name}' detected. Only read-only SELECT queries on sandbox benchmark tables are permitted.",
                )

        # 5. Check dangerous functions
        for fn_pattern in DANGEROUS_FUNCTIONS:
            if re.search(fn_pattern, clean_sql, flags=re.IGNORECASE):
                fn_name = fn_pattern.replace(r"\b", "")
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_DANGEROUS_FUNCTION",
                    error_message=f"Unapproved or dangerous function '{fn_name}' detected. Function calls that probe system internals or pause execution are blocked.",
                )

        # 6. Parse AST with sqlglot for structural analysis
        try:
            parsed = sqlglot.parse(clean_sql, read="postgres")
            if not parsed or len(parsed) != 1 or parsed[0] is None:
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_PARSE_ERROR",
                    error_message="Could not parse SQL statement into a single valid abstract syntax tree.",
                )

            expression = parsed[0]

            # 7. Must be a SELECT expression (or Union of Selects)
            if not isinstance(expression, (exp.Select, exp.Union)):
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_DML_DETECTED",
                    error_message=f"Expected a SELECT query expression, but found {type(expression).__name__}.",
                )

            # 8. Check join count
            joins = list(expression.find_all(exp.Join))
            if len(joins) > MAX_JOIN_COUNT:
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_EXCESSIVE_JOINS",
                    error_message=f"Query joins ({len(joins)}) exceed the maximum allowed sandbox complexity ({MAX_JOIN_COUNT} joins).",
                )

            # 9. Check AST nesting depth
            depth = cls._calculate_ast_depth(expression)
            if depth > MAX_NESTING_DEPTH:
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_EXCESSIVE_NESTING",
                    error_message=f"Query AST nesting depth ({depth}) exceeds sandbox limit ({MAX_NESTING_DEPTH}).",
                )

            # 10. Check relations against allowed benchmark tables
            allowlist = DATASET_ALLOWLISTS.get(dataset, ALL_SANDBOX_TABLES)
            tables_referenced = set()
            for table_node in expression.find_all(exp.Table):
                t_name = table_node.name.lower() if table_node.name else ""
                if t_name:
                    tables_referenced.add(t_name)

            # Ensure every referenced table is either in the specific dataset allowlist or general sandbox
            unauthorized = [tbl for tbl in tables_referenced if tbl not in allowlist and tbl not in ALL_SANDBOX_TABLES]
            if unauthorized:
                return SafetyValidationResult(
                    is_valid=False,
                    error_code="SAFETY_VIOLATION_UNAPPROVED_RELATION",
                    error_message=(
                        f"Query references unapproved table(s): {', '.join(unauthorized)}. "
                        f"Only sandbox benchmark tables in '{dataset}' are accessible."
                    ),
                )

        except Exception as e:
            return SafetyValidationResult(
                is_valid=False,
                error_code="SAFETY_VIOLATION_PARSE_ERROR",
                error_message=f"SQL AST parse error: {str(e)}",
            )

        return SafetyValidationResult(is_valid=True)

    @classmethod
    def _calculate_ast_depth(cls, node: exp.Expression, current: int = 1) -> int:
        max_depth = current
        for child in node.args.values():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, exp.Expression):
                        max_depth = max(max_depth, cls._calculate_ast_depth(c, current + 1))
            elif isinstance(child, exp.Expression):
                max_depth = max(max_depth, cls._calculate_ast_depth(child, current + 1))
        return max_depth
