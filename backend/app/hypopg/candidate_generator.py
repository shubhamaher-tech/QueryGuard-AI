"""
Index Candidate Generator and Validator for HypoPG Simulation

Supports single-column and composite B-tree candidates with strict ordering:
1. Equality filter columns first
2. Range filter columns second
3. Join keys third

Safety boundaries:
- Standard B-Tree only (no GiST/GIN/SP-GiST in this phase)
- Rejects expression indexes (e.g. LOWER(col), DATE_TRUNC)
- Rejects partial indexes (WHERE ...)
- Rejects UNIQUE indexes
- Disallows duplicate index patterns
"""

import re
from typing import List, Dict, Any, Tuple, Optional


DISALLOWED_INDEX_KEYWORDS = [
    "unique",
    "lower(",
    "upper(",
    "date_trunc(",
    "coalesce(",
    "where ",
    "using gin",
    "using gist",
    "using brin",
]


class IndexCandidate:
    def __init__(
        self,
        raw_table: str,
        raw_columns: List[str],
        tokenized_table: str,
        tokenized_columns: List[str],
        index_type: str = "BTREE",
        rationale: str = "",
    ):
        self.raw_table = raw_table
        self.raw_columns = raw_columns
        self.tokenized_table = tokenized_table
        self.tokenized_columns = tokenized_columns
        self.index_type = index_type
        self.rationale = rationale

    def generate_raw_ddl(self, index_name: Optional[str] = None) -> str:
        """
        Generates safe raw DDL to pass to hypopg_create_index.
        Never executed as real DDL on disk.
        """
        cols_str = ", ".join(self.raw_columns)
        idx = index_name or f"hidx_{self.raw_table}_{'_'.join(self.raw_columns[:2])}"
        return f"CREATE INDEX {idx} ON {self.raw_table} ({cols_str});"

    def get_tokenized_pattern(self) -> List[str]:
        return list(self.tokenized_columns)


class IndexCandidateValidator:
    """
    Validates index proposals against QueryGuard safety guardrails.
    """

    @classmethod
    def validate_candidate(
        cls,
        candidate_sql: str,
        columns: List[str],
    ) -> Tuple[bool, Optional[str]]:
        sql_lower = candidate_sql.lower()

        for kw in DISALLOWED_INDEX_KEYWORDS:
            if kw in sql_lower:
                return False, f"Disallowed index feature detected: '{kw}'. Only standard B-tree indexes are supported."

        if not columns or len(columns) == 0:
            return False, "Candidate must include at least one column."

        if len(columns) > 4:
            return False, "Candidate exceeds maximum of 4 composite index columns."

        # Expression check on column names
        for col in columns:
            if "(" in col or ")" in col or " " in col.strip():
                return False, f"Expression column '{col}' is not allowed in standard B-tree index."

        return True, None

    @classmethod
    def order_index_columns(
        cls,
        equality_cols: List[str],
        range_cols: List[str],
        join_cols: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Orders composite index columns by optimal B-tree selectivity:
        Equality -> Range -> Join
        """
        ordered: List[str] = []
        for c in equality_cols:
            if c not in ordered:
                ordered.append(c)
        for c in range_cols:
            if c not in ordered:
                ordered.append(c)
        if join_cols:
            for c in join_cols:
                if c not in ordered:
                    ordered.append(c)
        return ordered[:4]
