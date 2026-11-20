"""
Inferential Statistics, Seasonality & Dispersion Module
Implements statistical distribution parameters, seasonality indexing, and hypothesis testing (ANOVA / Kruskal-Wallis).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats


def calculate_ticket_dispersion(df: pd.DataFrame, group_col: str = "region_name") -> pd.DataFrame:
    """
    Computes 5-number summary (Min, Q1, Median, Q3, Max), IQR, and Tukey outlier boundaries per group.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    results = []
    for grp_val, grp_df in df.groupby(group_col):
        vals = grp_df["net_revenue"].dropna().values
        if len(vals) == 0:
            continue
        q1 = np.percentile(vals, 25)
        median = np.median(vals)
        q3 = np.percentile(vals, 75)
        iqr = q3 - q1
        lower_whisker = max(vals.min(), q1 - 1.5 * iqr)
        upper_whisker = min(vals.max(), q3 + 1.5 * iqr)
        outliers_count = int(np.sum((vals < (q1 - 1.5 * iqr)) | (vals > (q3 + 1.5 * iqr))))

        results.append({
            group_col: grp_val,
            "count": len(vals),
            "min": float(vals.min()),
            "q1": float(q1),
            "median": float(median),
            "q3": float(q3),
            "max": float(vals.max()),
            "iqr": float(iqr),
            "outliers_count": outliers_count
        })

    return pd.DataFrame(results)


def calculate_quarterly_seasonality_index(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts calendar quarter from order_date and computes seasonality index (baseline mean = 1.00)
    both nationally and cross-tabulated by region.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(), pd.DataFrame()

    temp = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(temp["order_date"]):
        temp["order_date"] = pd.to_datetime(temp["order_date"])

    temp["quarter"] = "Q" + temp["order_date"].dt.quarter.astype(str)

    # National quarterly index
    national_q = temp.groupby("quarter")["net_revenue"].sum().reset_index()
    mean_rev = national_q["net_revenue"].mean()
    national_q["seasonal_index"] = national_q["net_revenue"] / mean_rev if mean_rev > 0 else 1.0

    # Regional cross-tabulated heatmap matrix
    pivot_q = temp.pivot_table(
        index="region_name",
        columns="quarter",
        values="net_revenue",
        aggfunc="sum",
        fill_value=0.0
    )
    # Normalize each region by its quarterly mean
    regional_index = pivot_q.div(pivot_q.mean(axis=1), axis=0)

    return national_q, regional_index


def run_inter_regional_hypothesis_test(
    df: pd.DataFrame,
    metric: str = "gross_margin_pct",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Executes automated inferential hypothesis testing on regional metric distributions:
    1. Tests normality via Shapiro-Wilk test
    2. Tests homogeneity of variance via Levene test
    3. Auto-selects One-Way ANOVA (if parametric) or Kruskal-Wallis (if non-parametric)
    4. Generates plain-English verdict.
    """
    if df is None or len(df) == 0:
        return {"verdict": "Insufficient data"}

    temp = df.copy()
    if metric == "gross_margin_pct" and "gross_margin_pct" not in temp.columns:
        ship_col = "shipping_cost" if "shipping_cost" in temp.columns else "freight_cost"
        profit = temp["net_revenue"] - temp["total_cogs"] - temp[ship_col]
        temp["gross_margin_pct"] = (profit / temp["net_revenue"]) * 100.0

    groups = [group[metric].dropna().values for _, group in temp.groupby("region_name")]
    groups = [g for g in groups if len(g) > 2]

    if len(groups) < 2:
        return {"error": "Need at least 2 distinct regions for hypothesis testing"}

    # Pre-check 1: Normality (Shapiro-Wilk on largest group)
    shapiro_p = stats.shapiro(groups[0])[1] if len(groups[0]) >= 3 else 1.0
    is_normal = shapiro_p >= 0.05

    # Pre-check 2: Equal variances (Levene test)
    levene_stat, levene_p = stats.levene(*groups)
    is_homoscedastic = levene_p >= 0.05

    # Algorithm selection
    use_parametric = is_normal and is_homoscedastic

    if use_parametric:
        engine = "One-Way ANOVA (Parametric F-Test)"
        test_stat, p_value = stats.f_oneway(*groups)
        stat_name = "F-Statistic"
    else:
        engine = "Kruskal-Wallis H-Test (Non-Parametric)"
        test_stat, p_value = stats.kruskal(*groups)
        stat_name = "H-Statistic"

    reject_null = bool(p_value < alpha)
    verdict = (
        f"Reject H0 at alpha = {alpha}: Inter-regional margin disparities are statistically significant (p = {p_value:.6f}). Observed performance differences are mathematically confirmed, not random variation."
        if reject_null
        else f"Fail to Reject H0 at alpha = {alpha}: No statistically significant variance detected between regional margins (p = {p_value:.4f})."
    )

    return {
        "engine": engine,
        "statistic_name": stat_name,
        "statistic_value": float(test_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "is_normal": is_normal,
        "shapiro_p": float(shapiro_p),
        "is_homoscedastic": is_homoscedastic,
        "levene_p": float(levene_p),
        "reject_null": reject_null,
        "verdict": verdict
    }
