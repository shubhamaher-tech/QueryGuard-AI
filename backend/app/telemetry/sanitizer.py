"""
Privacy Sanitizer & HMAC-SHA256 Tokenization Engine for QueryGuard AI

Strictly enforces:
1. Zero raw SQL persistence or transmission.
2. Tenant-scoped HMAC-SHA256 identifier tokenization (tables, columns, aliases, indexes).
3. Literal masking (:INT, :NUMERIC, :STRING, :DATE, :TIMESTAMP).
4. Structural feature extraction.
5. Explicit privacy scanning before database persistence.
"""

import hmac
import hashlib
import re
from typing import Dict, Any, Tuple, List, Set, Optional
import sqlglot
from sqlglot import exp

from app.config import settings

KNOWN_PLAINTEXT_TABLES = {
    "regions",
    "customers",
    "products",
    "transactions",
    "order_items",
    "sales_transactions",
    "orders",
    "user_sessions",
    "audit_trail",
}

KNOWN_PLAINTEXT_COLUMNS = {
    "region_id",
    "transaction_date",
    "customer_id",
    "amount",
    "status",
    "product_id",
    "quantity",
    "unit_price",
    "region_code",
    "customer_code",
    "product_code",
    "category_code",
    "base_price",
    "stock_level",
    "credit_limit",
    "tier",
    "description",
    "transaction_ref",
    "line_total",
    "item_count",
    "total_tx_count",
    "total_amount",
    "avg_amount",
    "tx_count",
    "total_spent",
    "avg_spent",
}

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?")
COMMENT_REGEX = re.compile(r"(--[^\n]*|/\*[\s\S]*?\*/)")


def hmac_tokenize(identifier: str, prefix: str = "ID", secret: Optional[str] = None) -> str:
    """
    Computes a tenant-scoped deterministic HMAC-SHA256 token for an identifier.
    The same identifier with the same secret always produces the same token.
    Different identifiers produce different tokens.
    """
    key = (secret or settings.HMAC_TOKEN_SECRET).encode("utf-8")
    normalized = identifier.strip().lower().encode("utf-8")
    digest = hmac.new(key, normalized, hashlib.sha256).hexdigest()
    return f"{prefix}_{digest[:8].upper()}"


def tokenize_table(table_name: str, secret: Optional[str] = None) -> str:
    return hmac_tokenize(table_name, prefix="TBL", secret=secret)


def tokenize_column(column_name: str, secret: Optional[str] = None) -> str:
    return hmac_tokenize(column_name, prefix="COL", secret=secret)


def tokenize_alias(alias_name: str, secret: Optional[str] = None) -> str:
    return hmac_tokenize(alias_name, prefix="ALS", secret=secret)


def mask_literals_in_sql(raw_sql: str) -> str:
    """
    Replaces scalar literals with typed placeholders:
    - numbers become :INT or :NUMERIC
    - strings become :STRING
    - dates/timestamps become :DATE or :TIMESTAMP
    """
    if not raw_sql:
        return ""

    # 1. Strip raw SQL comments first
    sql_no_comments = COMMENT_REGEX.sub("", raw_sql)

    # 2. Try parsing with sqlglot for robust AST-based masking
    try:
        parsed = sqlglot.parse_one(sql_no_comments, read="postgres")

        def transform_node(node):
            if isinstance(node, exp.Literal):
                if node.is_string:
                    val = node.this
                    if DATE_REGEX.match(val):
                        return exp.var(":DATE")
                    return exp.var(":STRING")
                elif node.is_number:
                    if "." in str(node.this):
                        return exp.var(":NUMERIC")
                    return exp.var(":INT")
            return node

        transformed = parsed.transform(transform_node)
        sql = transformed.sql(dialect="postgres")
    except Exception:
        # Fallback to regex masking if sqlglot parse encounters partial fragments
        sql = sql_no_comments
        # Mask quoted dates
        sql = re.sub(r"'(?:\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?)'", ":DATE", sql)
        # Mask quoted strings
        sql = re.sub(r"'(?:[^'\\]|\\.)*'", ":STRING", sql)
        # Mask decimal numbers
        sql = re.sub(r"(?<=[^\w:])\d+\.\d+(?=[^\w]|$)", ":NUMERIC", sql)
        # Mask integers
        sql = re.sub(r"(?<=[^\w:])\b\d+\b(?=[^\w]|$)", ":INT", sql)

    return sql


def sanitize_benchmark_sql(raw_sql: str, secret: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
    """
    Full pipeline:
    1. Strip comments.
    2. Replace literals with typed placeholders (:INT, :NUMERIC, :STRING, :DATE).
    3. Tokenize tables, columns, and aliases using HMAC-SHA256.
    4. Return sanitized SQL template and token map.
    """
    if not raw_sql:
        return "", {}

    token_map: Dict[str, str] = {}
    sec = secret or settings.HMAC_TOKEN_SECRET

    # Step 1 & 2: Mask literals
    masked_sql = mask_literals_in_sql(raw_sql)

    # Step 3: Parse and tokenize schema identifiers with sqlglot
    try:
        parsed = sqlglot.parse_one(masked_sql, read="postgres")

        # Map tables
        for table in parsed.find_all(exp.Table):
            tbl_name = table.name
            if tbl_name and not tbl_name.startswith("TBL_"):
                tok = tokenize_table(tbl_name, secret=sec)
                token_map[tbl_name] = tok
                table.set("this", exp.to_identifier(tok))

        # Map columns
        for col in parsed.find_all(exp.Column):
            col_name = col.name
            if col_name and not col_name.startswith("COL_") and col_name not in {":INT", ":NUMERIC", ":STRING", ":DATE"}:
                tok = tokenize_column(col_name, secret=sec)
                token_map[col_name] = tok
                col.set("this", exp.to_identifier(tok))
            # Also tokenize table qualifier if present
            if col.table and not col.table.startswith("TBL_") and not col.table.startswith("ALS_"):
                tok_tbl = tokenize_alias(col.table, secret=sec)
                token_map[col.table] = tok_tbl
                col.set("table", exp.to_identifier(tok_tbl))

        # Map aliases
        for alias in parsed.find_all(exp.Alias):
            alias_name = alias.alias
            if alias_name and not alias_name.startswith("ALS_") and not alias_name.startswith("COL_"):
                tok = tokenize_alias(alias_name, secret=sec)
                token_map[alias_name] = tok
                alias.set("alias", exp.to_identifier(tok))

        sanitized_template = parsed.sql(dialect="postgres")
    except Exception:
        # Fallback dictionary-based regex tokenization
        sanitized_template = masked_sql
        for t in sorted(KNOWN_PLAINTEXT_TABLES, key=len, reverse=True):
            tok = tokenize_table(t, secret=sec)
            token_map[t] = tok
            sanitized_template = re.sub(rf"\b{re.escape(t)}\b", tok, sanitized_template, flags=re.IGNORECASE)

        for c in sorted(KNOWN_PLAINTEXT_COLUMNS, key=len, reverse=True):
            tok = tokenize_column(c, secret=sec)
            token_map[c] = tok
            sanitized_template = re.sub(rf"\b{re.escape(c)}\b", tok, sanitized_template, flags=re.IGNORECASE)

    # Clean double spaces
    sanitized_template = re.sub(r"\s+", " ", sanitized_template).strip()

    return sanitized_template, token_map


def scan_for_privacy_violations(sql: str) -> Tuple[bool, List[str]]:
    """
    Explicit Privacy Scanner.
    Rejects the telemetry event if any raw literal, quoted string,
    known plaintext table/column identifier, or comment is detected.
    """
    violations: List[str] = []

    # 1. Check for raw SQL comments
    if COMMENT_REGEX.search(sql):
        violations.append("Raw SQL comment detected")

    # 2. Check for quoted string literals
    if re.search(r"'[^']*'", sql):
        violations.append("Quoted string literal detected")

    # 3. Check for standalone unmasked numeric literals (ignoring placeholders and token hex digits)
    # Standalone numbers like 42, 100, 3.14 (not preceded by TBL_ or COL_ or ALS_ or colon)
    raw_num_match = re.search(r"(?<![A-Za-z0-9_:])\b\d+(\.\d+)?\b(?![A-Za-z0-9_])", sql)
    if raw_num_match:
        violations.append(f"Unmasked numeric literal detected: {raw_num_match.group(0)}")

    # 4. Check for known plaintext table names
    sql_lower = sql.lower()
    for table_name in KNOWN_PLAINTEXT_TABLES:
        if re.search(rf"\b{re.escape(table_name)}\b", sql_lower):
            violations.append(f"Plaintext table identifier detected: {table_name}")

    # 5. Check for known plaintext column names
    for col_name in KNOWN_PLAINTEXT_COLUMNS:
        if re.search(rf"\b{re.escape(col_name)}\b", sql_lower):
            violations.append(f"Plaintext column identifier detected: {col_name}")

    is_passed = len(violations) == 0
    return is_passed, violations


def compute_query_fingerprint(sanitized_template: str, secret: Optional[str] = None) -> str:
    """
    Generates a deterministic HMAC query fingerprint from the sanitized template.
    """
    sec = (secret or settings.HMAC_TOKEN_SECRET).encode("utf-8")
    normalized = sanitized_template.strip().lower().encode("utf-8")
    return f"fp_hmac_{hmac.new(sec, normalized, hashlib.sha256).hexdigest()[:16]}"


# Bucket helpers for telemetry categorization
def bucket_latency(ms: float) -> str:
    if ms < 10.0:
        return "<10ms"
    elif ms < 100.0:
        return "10ms-100ms"
    elif ms < 500.0:
        return "100ms-500ms"
    elif ms < 1000.0:
        return "500ms-1s"
    elif ms < 5000.0:
        return "1s-5s"
    return ">5s"


def bucket_calls(calls: int) -> str:
    if calls <= 10:
        return "1-10"
    elif calls <= 50:
        return "11-50"
    elif calls <= 200:
        return "51-200"
    elif calls <= 1000:
        return "201-1000"
    return ">1000"


def bucket_rows(rows: int) -> str:
    if rows < 1000:
        return "<1k"
    elif rows < 10000:
        return "1k-10k"
    elif rows < 100000:
        return "10k-100k"
    elif rows < 500000:
        return "100k-500k"
    elif rows < 1000000:
        return "500k-1M"
    return ">1M"


def bucket_cost(cost: float) -> str:
    if cost < 1000.0:
        return "<1k"
    elif cost < 10000.0:
        return "1k-10k"
    elif cost < 50000.0:
        return "10k-50k"
    elif cost < 100000.0:
        return "50k-100k"
    return ">100k"
