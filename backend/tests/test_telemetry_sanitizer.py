import pytest
from app.telemetry.sanitizer import (
    hmac_tokenize,
    tokenize_table,
    tokenize_column,
    mask_literals_in_sql,
    sanitize_benchmark_sql,
    scan_for_privacy_violations,
    compute_query_fingerprint,
)


def test_hmac_token_stability():
    secret_a = "tenant-secret-alpha-123"
    secret_b = "tenant-secret-beta-456"

    # Same input + same secret -> same token
    tok1 = hmac_tokenize("transactions", prefix="TBL", secret=secret_a)
    tok2 = hmac_tokenize("transactions", prefix="TBL", secret=secret_a)
    assert tok1 == tok2
    assert tok1.startswith("TBL_")

    # Case insensitivity & trimming
    tok3 = hmac_tokenize("  TRANSACTIONS  ", prefix="TBL", secret=secret_a)
    assert tok1 == tok3

    # Different identifier -> different token
    tok_cust = hmac_tokenize("customers", prefix="TBL", secret=secret_a)
    assert tok1 != tok_cust

    # Different secret -> different token
    tok_diff_secret = hmac_tokenize("transactions", prefix="TBL", secret=secret_b)
    assert tok1 != tok_diff_secret


def test_literal_masking_comprehensive():
    # Integer, decimal, string, date, timestamp, IN-list, and NULL
    raw_query = """
    SELECT id, amount, status 
    FROM transactions 
    WHERE region_id = 42 
      AND amount > 199.95 
      AND status = 'COMPLETED' 
      AND transaction_date >= '2025-06-01'
      AND created_at <= '2025-06-01 12:30:00'
      AND customer_id IN (101, 102, 103)
      AND notes IS NOT NULL;
    """
    masked = mask_literals_in_sql(raw_query)

    # Assertions
    assert "42" not in masked
    assert "199.95" not in masked
    assert "'COMPLETED'" not in masked
    assert "'2025-06-01'" not in masked
    assert ":INT" in masked or ":NUMERIC" in masked
    assert ":DATE" in masked or ":STRING" in masked
    assert "IS NOT NULL" in masked  # Preserved syntax keyword


def test_privacy_scanner_rejects_violations():
    # 1. Rejects raw numeric literal
    dirty_sql_num = "SELECT * FROM TBL_A1 WHERE COL_B2 = 42"
    passed, violations = scan_for_privacy_violations(dirty_sql_num)
    assert passed is False
    assert any("numeric literal" in v.lower() for v in violations)

    # 2. Rejects quoted string literal
    dirty_sql_str = "SELECT * FROM TBL_A1 WHERE COL_B2 = 'confidential'"
    passed, violations = scan_for_privacy_violations(dirty_sql_str)
    assert passed is False
    assert any("quoted string" in v.lower() for v in violations)

    # 3. Rejects known plaintext table identifiers
    dirty_sql_tbl = "SELECT * FROM transactions WHERE COL_B2 = :INT"
    passed, violations = scan_for_privacy_violations(dirty_sql_tbl)
    assert passed is False
    assert any("table identifier" in v.lower() for v in violations)

    # 4. Rejects known plaintext column identifiers
    dirty_sql_col = "SELECT customer_id FROM TBL_A1 WHERE COL_B2 = :INT"
    passed, violations = scan_for_privacy_violations(dirty_sql_col)
    assert passed is False
    assert any("column identifier" in v.lower() for v in violations)

    # 5. Rejects raw SQL comments
    dirty_sql_comment = "SELECT * FROM TBL_A1 -- secret raw developer note"
    passed, violations = scan_for_privacy_violations(dirty_sql_comment)
    assert passed is False
    assert any("comment" in v.lower() for v in violations)

    # 6. Passes cleanly on sanitized template
    clean_sql = "SELECT COL_8A2F FROM TBL_3F1A WHERE COL_9C1B = :INT AND COL_4E2A >= :DATE"
    passed, violations = scan_for_privacy_violations(clean_sql)
    assert passed is True
    assert len(violations) == 0


def test_sanitize_benchmark_sql_pipeline():
    raw_benchmark = """
    -- Benchmark query 1: regional volume
    SELECT region_id, count(*), sum(amount)
    FROM transactions
    WHERE region_id = 5 AND transaction_date >= '2025-06-01'
    GROUP BY region_id;
    """
    sanitized, token_map = sanitize_benchmark_sql(raw_benchmark)

    # No comments
    assert "--" not in sanitized
    # No raw literals
    assert "= 5" not in sanitized
    assert "= :INT" in sanitized or "= %(INT)s" in sanitized
    assert "'2025-06-01'" not in sanitized
    # Tokenized table
    assert "transactions" not in sanitized
    assert any(k in token_map for k in ["transactions", "region_id"])
    assert "TBL_" in sanitized

    # Check privacy scanner verification
    passed, violations = scan_for_privacy_violations(sanitized)
    assert passed is True
    assert len(violations) == 0
