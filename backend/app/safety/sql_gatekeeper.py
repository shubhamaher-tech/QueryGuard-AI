import re
from typing import Tuple, List, Optional
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
]

DANGEROUS_FUNCTIONS = [
    r"\bpg_sleep\b",
    r"\bpg_read_file\b",
    r"\bpg_write_file\b",
    r"\bpg_terminate_backend\b",
    r"\bdblink\b",
    r"\bquery_to_xml\b",
    r"\bversion\b",
    r"\bcurrent_user\b",
    r"\bsystem_user\b",
]

MAX_SQL_LENGTH = 4000
MAX_JOIN_COUNT = 10
MAX_NESTING_DEPTH = 8

class SQLGatekeeper:
    """
    Validates SQL safety before any execution or simulation.
    Ensures rewrites are strictly read-only, non-destructive, single-statement SELECTs.
    """

    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        if not sql or not sql.strip():
            return False, "SQL statement is empty."

        clean_sql = sql.strip()

        # 1. Length check
        if len(clean_sql) > MAX_SQL_LENGTH:
            return False, f"SQL statement exceeds maximum length of {MAX_SQL_LENGTH} characters."

        # 2. Reject comments
        if "--" in clean_sql or "/*" in clean_sql or "*/" in clean_sql:
            return False, "SQL comments are strictly forbidden in rewrite candidates."

        # 3. Reject multi-statement (semicolon inside or multiple queries)
        # Strip trailing semicolon
        semicolon_stripped = clean_sql.rstrip(";").strip()
        if ";" in semicolon_stripped:
            return False, "Multi-statement execution is strictly forbidden."

        # 4. Check forbidden keywords
        for kw_pattern in FORBIDDEN_KEYWORDS:
            if re.search(kw_pattern, clean_sql, flags=re.IGNORECASE):
                kw_name = kw_pattern.replace(r"\b", "")
                return False, f"Forbidden keyword detected: {kw_name}. Only read-only SELECT statements are allowed."

        # 5. Check dangerous functions
        for fn_pattern in DANGEROUS_FUNCTIONS:
            if re.search(fn_pattern, clean_sql, flags=re.IGNORECASE):
                fn_name = fn_pattern.replace(r"\b", "")
                return False, f"Unapproved function detected: {fn_name}."

        # 6. AST Parsing with sqlglot
        try:
            parsed = sqlglot.parse(clean_sql, read="postgres")
            if not parsed or len(parsed) != 1 or parsed[0] is None:
                return False, "Failed to parse SQL AST or multiple statements detected."

            expression = parsed[0]

            # 7. Must be a SELECT expression
            if not isinstance(expression, exp.Select):
                return False, f"Expected a SELECT query, but got {type(expression).__name__}."

            # 8. Check join count
            joins = list(expression.find_all(exp.Join))
            if len(joins) > MAX_JOIN_COUNT:
                return False, f"Join count ({len(joins)}) exceeds maximum permitted threshold ({MAX_JOIN_COUNT})."

            # 9. Check nesting depth
            depth = self._calculate_ast_depth(expression)
            if depth > MAX_NESTING_DEPTH:
                return False, f"AST nesting depth ({depth}) exceeds maximum limit ({MAX_NESTING_DEPTH})."

        except Exception as e:
            return False, f"SQL syntax or AST validation failed: {str(e)}"

        return True, None

    def _calculate_ast_depth(self, node: exp.Expression, current: int = 1) -> int:
        max_depth = current
        for child in node.args.values():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, exp.Expression):
                        max_depth = max(max_depth, self._calculate_ast_depth(c, current + 1))
            elif isinstance(child, exp.Expression):
                max_depth = max(max_depth, self._calculate_ast_depth(child, current + 1))
        return max_depth

sql_gatekeeper = SQLGatekeeper()
