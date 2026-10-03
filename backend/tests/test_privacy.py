import pytest
from app.privacy import mask_literals, tokenize_identifiers, sanitize_sql, is_anonymized, PRIVACY_STATEMENT


def test_sql_literal_masking_integers_and_dates():
    sql = "SELECT * FROM orders WHERE amount > 100 AND created_at >= '2026-09-01';"
    masked = mask_literals(sql)
    assert ":INT" in masked or ":NUM" in masked
    assert ":DATE" in masked
    assert "'2026-09-01'" not in masked
    assert "100" not in masked


def test_sql_identifier_tokenization():
    sql = "SELECT region_id, transaction_date FROM sales_transactions"
    tokenized, mapping = tokenize_identifiers(sql)
    assert "TBL_A12" in tokenized
    assert "COL_R01" in tokenized
    assert "COL_D02" in tokenized
    assert "sales_transactions" not in tokenized


def test_sanitize_sql_full_pipeline_matches_specification():
    raw_input = """SELECT * FROM sales_transactions
WHERE region_id = 42
AND transaction_date >= '2026-09-01';"""

    sanitized = sanitize_sql(raw_input)

    # Verify token replacements
    assert "TBL_A12" in sanitized
    assert "COL_R01 = :INT" in sanitized
    assert "COL_D02 >= :DATE" in sanitized

    # Verify no raw literals or sensitive identifiers exist
    assert "sales_transactions" not in sanitized
    assert "region_id" not in sanitized
    assert "transaction_date" not in sanitized
    assert "42" not in sanitized
    assert "'2026-09-01'" not in sanitized


def test_is_anonymized_safeguard():
    safe_sql = "SELECT COL_R01 FROM TBL_A12 WHERE COL_D02 >= :DATE"
    assert is_anonymized(safe_sql) is True

    unsafe_literal_sql = "SELECT COL_R01 FROM TBL_A12 WHERE COL_D02 >= '2026-09-01'"
    assert is_anonymized(unsafe_literal_sql) is False

    unsafe_table_sql = "SELECT COL_R01 FROM sales_transactions WHERE COL_D02 >= :DATE"
    assert is_anonymized(unsafe_table_sql) is False
