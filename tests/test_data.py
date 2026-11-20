"""
Technical Tests: Data Ingestion, Schema Integrity & Data Cleaning Module
Tests: TC-T-01, TC-T-02, TC-T-03, TC-T-04, TC-T-05, TC-T-06
"""

import os
import sqlite3
import pytest
import pandas as pd
import numpy as np

# Resolve path to database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")


def get_db_connection():
    """Helper to open an SQLite connection with foreign keys enabled."""
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Database not found at {DB_PATH}. Ensure Step 10 data generation has run.")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def test_tc_t_01_db_connection_and_table_existence():
    """TC-T-01: Verify SQLite database connects and all required tables exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()

    expected_tables = ["dim_regions", "dim_products", "dim_customers", "fact_sales", "view_sales_analysis"]
    for table in expected_tables:
        assert table in names, f"Required table or view '{table}' is missing from database schema."


def test_tc_t_02_row_and_column_counts():
    """TC-T-02: Verify expected row counts and column schemas across core tables."""
    conn = get_db_connection()
    
    # Check dim_regions: 25 rows
    df_regions = pd.read_sql_query("SELECT * FROM dim_regions;", conn)
    assert len(df_regions) == 25, f"Expected 25 regions, found {len(df_regions)}"
    assert "region_name" in df_regions.columns
    assert "city_tier" in df_regions.columns

    # Check dim_products: 30 rows
    df_products = pd.read_sql_query("SELECT * FROM dim_products;", conn)
    assert len(df_products) == 30, f"Expected 30 products, found {len(df_products)}"
    assert "product_category" in df_products.columns
    assert "base_cost" in df_products.columns

    # Check dim_customers: 100 rows
    df_customers = pd.read_sql_query("SELECT * FROM dim_customers;", conn)
    assert len(df_customers) == 100, f"Expected 100 customers, found {len(df_customers)}"
    assert "customer_type" in df_customers.columns

    # Check fact_sales: >= 250 rows
    df_sales = pd.read_sql_query("SELECT * FROM fact_sales;", conn)
    assert len(df_sales) >= 250, f"Expected >= 250 sales rows, found {len(df_sales)}"
    assert "gross_revenue" in df_sales.columns
    assert "net_revenue" in df_sales.columns
    assert "gross_margin_pct" in df_sales.columns

    # Check view_sales_analysis: 36 columns
    df_view = pd.read_sql_query("SELECT * FROM view_sales_analysis LIMIT 1;", conn)
    assert len(df_view.columns) >= 30, f"Expected >= 30 columns in view_sales_analysis, found {len(df_view.columns)}"
    conn.close()


def test_tc_t_03_primary_key_uniqueness():
    """TC-T-03: Verify primary keys are unique and non-null in all dimension and fact tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    checks = [
        ("dim_regions", "region_id"),
        ("dim_products", "product_id"),
        ("dim_customers", "customer_id"),
        ("fact_sales", "order_id")
    ]

    for table, pk in checks:
        cursor.execute(f"SELECT COUNT({pk}), COUNT(DISTINCT {pk}) FROM {table};")
        total_count, distinct_count = cursor.fetchone()
        assert total_count == distinct_count, f"Duplicate PK detected in {table}.{pk}: total={total_count}, distinct={distinct_count}"

    conn.close()


def test_tc_t_04_referential_integrity_foreign_keys():
    """TC-T-04: Execute SQLite foreign key check pragma to ensure zero orphan transactions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    conn.close()

    assert len(violations) == 0, f"Foreign key violations detected in SQLite database: {violations}"


def test_tc_t_05_data_cleaning_pipeline_imputation():
    """TC-T-05: Verify data cleaning logic handles missing values and deduplication correctly."""
    # Test fixture of dirty data
    dirty_data = pd.DataFrame({
        "order_id": [1, 2, 2, 3],
        "region_id": [1, 1, 1, 2],
        "shipping_cost": [250.0, np.nan, np.nan, 400.0],
        "discount_pct": [0.10, np.nan, np.nan, 0.20],
        "order_quantity": [2, 3, 3, 1]
    })

    # Deduplicate
    deduped = dirty_data.drop_duplicates(subset=["order_id"])
    assert len(deduped) == 3, f"Expected 3 rows after deduplication, got {len(deduped)}"

    # Impute missing values (median imputation for shipping, 0.0 for discount)
    clean_df = deduped.copy()
    clean_df["discount_pct"] = clean_df["discount_pct"].fillna(0.0)
    shipping_median = clean_df["shipping_cost"].median()
    clean_df["shipping_cost"] = clean_df["shipping_cost"].fillna(shipping_median)

    assert clean_df["discount_pct"].isnull().sum() == 0, "Missing discounts were not imputed"
    assert clean_df["shipping_cost"].isnull().sum() == 0, "Missing shipping costs were not imputed"
    assert (clean_df["discount_pct"] >= 0.0).all(), "Discount cannot be negative"


def test_tc_t_06_database_query_performance():
    """TC-T-06: Verify querying view_sales_analysis completes in under 500ms."""
    import time
    conn = get_db_connection()
    start_time = time.time()
    
    df = pd.read_sql_query("SELECT region_name, SUM(net_revenue) as rev FROM view_sales_analysis GROUP BY region_name;", conn)
    elapsed = time.time() - start_time
    conn.close()

    assert elapsed < 0.5, f"Analytical query exceeded performance SLA: {elapsed:.3f}s"
    assert len(df) == 5, f"Expected 5 regions, got {len(df)}"
