"""
Pareto Analysis & Category Contribution Module
Implements 80/20 cumulative contribution calculations and Vital Few vs Trivial Many segmentation.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_category_pareto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks product categories by descending net revenue, computes cumulative revenue,
    calculates cumulative percentage, and classifies categories into:
    - 'Vital Few (Tier A)' for cumulative <= 80% (plus the intersecting boundary)
    - 'Trivial Many (Tier B)' for the long tail.
    
    Returns:
        Sorted DataFrame with columns: [product_category, net_revenue, revenue_pct, cum_revenue, cum_pct, pareto_tier]
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    total_net = df["net_revenue"].sum()
    cat_df = df.groupby("product_category").agg(
        net_revenue=("net_revenue", "sum"),
        order_count=("order_id", "nunique"),
        avg_price=("unit_price", "mean")
    ).reset_index()

    # Sort descending by net revenue
    cat_df = cat_df.sort_values(by="net_revenue", ascending=False).reset_index(drop=True)
    cat_df["revenue_pct"] = (cat_df["net_revenue"] / total_net) * 100.0 if total_net > 0 else 0.0
    cat_df["cum_revenue"] = cat_df["net_revenue"].cumsum()
    cat_df["cum_pct"] = (cat_df["cum_revenue"] / total_net) * 100.0 if total_net > 0 else 0.0

    # Classify Tier A vs Tier B
    # A category is Tier A if its start was <= 80%
    prev_cum = cat_df["cum_pct"].shift(1).fillna(0.0)
    cat_df["pareto_tier"] = np.where(prev_cum < 80.0, "Vital Few (Tier A)", "Trivial Many (Tier B)")

    return cat_df
