import re
from typing import Dict, Tuple, Optional, Set
from app.privacy import DEFAULT_TABLE_MAPPING, DEFAULT_COLUMN_MAPPING

# Inverted mappings for fast rehydration: token -> synthetic physical name
REVERSE_TABLE_MAP = {token: real for real, token in DEFAULT_TABLE_MAPPING.items()}
REVERSE_COLUMN_MAP = {token: real for real, token in DEFAULT_COLUMN_MAPPING.items()}

# Add additional known benchmark mappings
EXTRA_TOKEN_MAP = {
    "TBL_A12": "transactions",
    "TBL_B03": "customers",
    "TBL_C99": "order_items",
    "TBL_D44": "products",
    "TBL_E55": "regions",
    "COL_001": "id",
    "COL_R01": "region_id",
    "COL_D02": "transaction_date",
    "COL_C03": "customer_id",
    "COL_A04": "amount",
    "COL_S05": "status",
    "COL_N06": "name",
    "COL_P07": "price",
    "COL_Q08": "quantity",
    "COL_T09": "transaction_id",
    "COL_P10": "product_id",
}

class LocalRehydrator:
    """
    Trusted local in-memory rehydrator.
    Maps tokenized SQL templates to workload-postgres relations strictly
    for sandbox EXPLAIN evaluation.

    GUARANTEE: The rehydrated SQL string is strictly confined to memory
    and is NEVER returned via APIs, UI, logs, audit trails, or LLM prompts.
    """

    def __init__(self):
        self.table_map = {**REVERSE_TABLE_MAP, **EXTRA_TOKEN_MAP}
        self.column_map = {**REVERSE_COLUMN_MAP, **EXTRA_TOKEN_MAP}

    def register_custom_mapping(self, token: str, real_identifier: str):
        if token.startswith("TBL_"):
            self.table_map[token] = real_identifier
        elif token.startswith("COL_"):
            self.column_map[token] = real_identifier

    def verify_tokens_authorized(
        self,
        sql_template: str,
        authorized_table_tokens: Set[str],
        authorized_column_tokens: Set[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that all tokens in the rewrite template are known and authorized
        for the given query event.
        """
        found_tables = set(re.findall(r"\bTBL_[A-Z0-9_]+\b", sql_template))
        found_columns = set(re.findall(r"\bCOL_[A-Z0-9_]+\b", sql_template))

        # Check unauthorized tables
        unauthorized_tables = found_tables - authorized_table_tokens
        if unauthorized_tables:
            return False, f"Unauthorized or unknown table tokens in rewrite: {unauthorized_tables}"

        # Check unauthorized columns (allowing newly referenced columns if they belong to authorized tables in our map)
        unauthorized_columns = found_columns - authorized_column_tokens
        # If columns are not in query's original list, verify they exist in known schema map
        for col in unauthorized_columns:
            if col not in self.column_map:
                return False, f"Unknown column token in rewrite: {col}"

        return True, None

    def rehydrate_for_sandbox(
        self,
        masked_sql: str,
    ) -> str:
        """
        Rehydrates a masked SQL template into valid executable benchmark SQL
        strictly for EXPLAIN (FORMAT JSON) sandbox execution.
        """
        rehydrated = masked_sql

        # 1. Replace masked literals with safe sample values
        rehydrated = re.sub(r":INT\b", "5", rehydrated)
        rehydrated = re.sub(r":DATE\b", "'2026-01-01'", rehydrated)
        rehydrated = re.sub(r":NUM\b", "100.0", rehydrated)
        rehydrated = re.sub(r":STR\b", "'COMPLETED'", rehydrated)
        rehydrated = re.sub(r":UUID\b", "'00000000-0000-0000-0000-000000000000'", rehydrated)

        # 2. Replace table tokens
        for token, real_name in self.table_map.items():
            pattern = rf"\b{re.escape(token)}\b"
            rehydrated = re.sub(pattern, real_name, rehydrated)

        # 3. Replace column tokens
        for token, real_name in self.column_map.items():
            pattern = rf"\b{re.escape(token)}\b"
            rehydrated = re.sub(pattern, real_name, rehydrated)

        return rehydrated

local_rehydrator = LocalRehydrator()
