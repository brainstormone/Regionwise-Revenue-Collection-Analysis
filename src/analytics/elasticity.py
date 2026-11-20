"""
Discount Elasticity & Margin Degradation Analytics
Bins transactions into promotional brackets and computes linear regression slope.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy import stats


def calculate_discount_brackets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bins orders into 4 promotional discount depth brackets:
    - 0-10% (Low / Baseline)
    - 11-20% (Moderate)
    - 21-30% (High Promotional)
    - >30% (Aggressive Clearance)
    
    Computes order volume, average margin %, total revenue, and deficient order count per bracket.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    temp_df = df.copy()
    bins = [-0.01, 0.10, 0.20, 0.30, 1.00]
    labels = ["0-10% (Low)", "11-20% (Moderate)", "21-30% (High)", ">30% (Clearance)"]
    temp_df["discount_bracket"] = pd.cut(temp_df["discount_pct"], bins=bins, labels=labels)

    ship_col = "shipping_cost" if "shipping_cost" in temp_df.columns else "freight_cost"
    if "gross_margin_pct" not in temp_df.columns:
        profit = temp_df["net_revenue"] - temp_df["total_cogs"] - temp_df[ship_col]
        temp_df["gross_margin_pct"] = (profit / temp_df["net_revenue"]) * 100.0

    bracket_df = temp_df.groupby("discount_bracket", observed=False).agg(
        order_count=("order_id", "count"),
        total_net_rev=("net_revenue", "sum"),
        avg_discount_pct=("discount_pct", "mean"),
        avg_gross_margin=("gross_margin_pct", "mean"),
        deficient_orders=("gross_margin_pct", lambda x: (x < 15.0).sum())
    ).reset_index()

    bracket_df["deficient_rate_pct"] = (
        bracket_df["deficient_orders"] / bracket_df["order_count"] * 100.0
    ).fillna(0.0)

    return bracket_df


def calculate_ols_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes Ordinary Least Squares (OLS) linear regression of Gross Margin % on Discount %.
    Returns slope, intercept, r-value, p-value, and std_err.
    """
    if df is None or len(df) < 5:
        return {"slope": 0.0, "intercept": 0.0, "r_squared": 0.0, "p_value": 1.0}

    ship_col = "shipping_cost" if "shipping_cost" in df.columns else "freight_cost"
    profit = df["net_revenue"] - df["total_cogs"] - df[ship_col]
    margin = (profit / df["net_revenue"]) * 100.0
    discount = df["discount_pct"] * 100.0  # as percentage

    valid_mask = ~(discount.isnull() | margin.isnull())
    x = discount[valid_mask].values
    y = margin[valid_mask].values

    slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_value": float(r_val),
        "r_squared": float(r_val ** 2),
        "p_value": float(p_val),
        "std_err": float(std_err)
    }
