"""
Financial KPIs & Profitability Calculations Module
Calculates macro revenues, gross margins, regional contribution ratios, and margin deficiency flags.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_macro_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates macro enterprise KPIs: Gross Revenue, Net Revenue, COGS, Freight,
    Overall Gross Margin %, Total Orders, and Average Order Value (AOV).
    """
    if df is None or len(df) == 0:
        return {
            "gross_revenue": 0.0,
            "net_revenue": 0.0,
            "total_cogs": 0.0,
            "shipping_cost": 0.0,
            "gross_profit": 0.0,
            "gross_margin_pct": 0.0,
            "total_orders": 0,
            "aov": 0.0
        }

    gross_rev = float(df["gross_revenue"].sum())
    net_rev = float(df["net_revenue"].sum())
    cogs = float(df["total_cogs"].sum()) if "total_cogs" in df.columns else 0.0
    
    ship_col = "shipping_cost" if "shipping_cost" in df.columns else "freight_cost"
    freight = float(df[ship_col].sum()) if ship_col in df.columns else 0.0
    
    gross_profit = net_rev - cogs - freight
    gross_margin_pct = (gross_profit / net_rev * 100.0) if net_rev > 0 else 0.0
    total_orders = int(df["order_id"].nunique()) if "order_id" in df.columns else len(df)
    aov = (net_rev / total_orders) if total_orders > 0 else 0.0

    return {
        "gross_revenue": gross_rev,
        "net_revenue": net_rev,
        "total_cogs": cogs,
        "shipping_cost": freight,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "total_orders": total_orders,
        "aov": aov
    }


def calculate_regional_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates net revenue, gross revenue, order volume, and calculates
    percentage contribution to national total per region.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    total_net = df["net_revenue"].sum()
    ship_col = "shipping_cost" if "shipping_cost" in df.columns else "freight_cost"
    
    reg_summary = df.groupby("region_name").agg(
        gross_revenue=("gross_revenue", "sum"),
        net_revenue=("net_revenue", "sum"),
        total_cogs=("total_cogs", "sum"),
        shipping_cost=(ship_col, "sum"),
        order_count=("order_id", "nunique"),
        avg_ticket=("net_revenue", "mean")
    ).reset_index()

    reg_summary["gross_profit"] = reg_summary["net_revenue"] - reg_summary["total_cogs"] - reg_summary["shipping_cost"]
    reg_summary["gross_margin_pct"] = (reg_summary["gross_profit"] / reg_summary["net_revenue"]) * 100.0
    reg_summary["revenue_pct"] = (reg_summary["net_revenue"] / total_net) * 100.0 if total_net > 0 else 0.0

    # Sort descending by net revenue
    reg_summary = reg_summary.sort_values(by="net_revenue", ascending=False).reset_index(drop=True)
    return reg_summary


def flag_margin_deficiency(df: pd.DataFrame, hurdle: float = 15.0) -> pd.DataFrame:
    """
    Labels each order as 'Healthy' or 'Margin Deficient' based on the 15.0% hurdle rate.
    """
    if df is None or len(df) == 0:
        return df

    out_df = df.copy()
    if "gross_margin_pct" not in out_df.columns:
        ship_col = "shipping_cost" if "shipping_cost" in out_df.columns else "freight_cost"
        out_df["gross_profit"] = out_df["net_revenue"] - out_df["total_cogs"] - out_df[ship_col]
        out_df["gross_margin_pct"] = (out_df["gross_profit"] / out_df["net_revenue"]) * 100.0

    out_df["margin_status"] = np.where(out_df["gross_margin_pct"] >= hurdle, "Healthy", "Margin Deficient")
    return out_df
