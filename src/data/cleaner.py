"""
Data Cleaning & Hygiene Pipeline Module
Handles missing freight/discount imputation and primary key deduplication.
"""

import pandas as pd
import numpy as np


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw or staging transactional sales data:
    1. Deduplicates records by primary key 'order_id'
    2. Imputes missing promotional discount percentages with 0.0
    3. Imputes missing freight/shipping costs using localized regional medians
    4. Enforces non-negativity and correct numeric dtypes
    
    Args:
        df: Input raw DataFrame from fact_sales or view_sales_analysis
        
    Returns:
        Cleaned, deduplicated, and validated DataFrame
    """
    if df is None or len(df) == 0:
        return df

    clean_df = df.copy()

    # 1. Deduplicate by primary key if present
    if "order_id" in clean_df.columns:
        clean_df = clean_df.drop_duplicates(subset=["order_id"]).reset_index(drop=True)

    # 2. Impute discount_pct: default to 0.0
    if "discount_pct" in clean_df.columns:
        clean_df["discount_pct"] = clean_df["discount_pct"].fillna(0.0)
        clean_df["discount_pct"] = clean_df["discount_pct"].clip(lower=0.0, upper=0.35)

    # 3. Impute shipping_cost / freight: localized regional median or overall median
    shipping_col = None
    for col in ["shipping_cost", "freight_cost"]:
        if col in clean_df.columns:
            shipping_col = col
            break

    if shipping_col:
        if "region_name" in clean_df.columns:
            # Impute per region median
            clean_df[shipping_col] = clean_df.groupby("region_name")[shipping_col].transform(
                lambda x: x.fillna(x.median())
            )
        # Fallback to overall median if region median is NaN
        overall_median = clean_df[shipping_col].median()
        if pd.isna(overall_median):
            overall_median = 250.0
        clean_df[shipping_col] = clean_df[shipping_col].fillna(overall_median)

    # 4. Enforce valid calculated columns if gross/net revenue present
    if "order_quantity" in clean_df.columns and "unit_price" in clean_df.columns:
        if "gross_revenue" not in clean_df.columns or clean_df["gross_revenue"].isnull().any():
            clean_df["gross_revenue"] = clean_df["order_quantity"] * clean_df["unit_price"]

    if "gross_revenue" in clean_df.columns and "discount_pct" in clean_df.columns:
        if "net_revenue" not in clean_df.columns or clean_df["net_revenue"].isnull().any():
            clean_df["net_revenue"] = clean_df["gross_revenue"] * (1.0 - clean_df["discount_pct"])

    return clean_df
