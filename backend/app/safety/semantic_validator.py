from typing import Tuple, Optional, List
import sqlglot
from sqlglot import exp

class SemanticValidator:
    """
    Validates structural and semantic equivalence between the original
    masked SQL query and the proposed rewrite candidate.
    """

    def validate_equivalence(
        self,
        original_sql: str,
        rewritten_sql: str,
    ) -> Tuple[bool, Optional[str]]:
        try:
            parsed_orig = sqlglot.parse(original_sql, read="postgres")
            parsed_rewr = sqlglot.parse(rewritten_sql, read="postgres")

            if not parsed_orig or not parsed_rewr:
                return False, "Failed to parse AST for original or rewritten SQL."

            exp_orig = parsed_orig[0]
            exp_rewr = parsed_rewr[0]

            if not isinstance(exp_orig, exp.Select) or not isinstance(exp_rewr, exp.Select):
                return False, "Both original and rewrite queries must be SELECT expressions."

            # 1. Compare projected column count (if not wildcard SELECT *)
            orig_selects = exp_orig.expressions
            rewr_selects = exp_rewr.expressions

            has_orig_star = any(isinstance(e, exp.Star) for e in orig_selects)
            has_rewr_star = any(isinstance(e, exp.Star) for e in rewr_selects)

            if not has_orig_star and not has_rewr_star:
                if len(orig_selects) != len(rewr_selects):
                    return (
                        False,
                        f"Projected column count mismatch: original has {len(orig_selects)} columns, "
                        f"rewrite has {len(rewr_selects)} columns.",
                    )

            # 2. Verify from/join tables in rewrite exist in original or schema
            orig_tables = {t.name for t in exp_orig.find_all(exp.Table) if t.name}
            rewr_tables = {t.name for t in exp_rewr.find_all(exp.Table) if t.name}

            # Rewrite should not query entirely unrelated tables
            if not rewr_tables.issubset(orig_tables):
                # Allow if only table alias changes
                extra_tables = rewr_tables - orig_tables
                # If extra table is not an alias or recognized table token
                for et in extra_tables:
                    if not et.startswith("TBL_") and not et.startswith("ALIAS_"):
                        return False, f"Rewrite queries unauthorized relation: {et}"

            return True, None

        except Exception as e:
            return False, f"Semantic equivalence check failed: {str(e)}"

semantic_validator = SemanticValidator()
