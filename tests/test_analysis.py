"""
Technical Tests: Business Logic, Analytical Formulas & Inferential Statistics
Tests: TC-T-07, TC-T-08, TC-T-09, TC-T-10, TC-T-11, TC-T-12
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats


def test_tc_t_07_gross_revenue_and_net_revenue_formula():
    """TC-T-07: Verify financial revenue calculation on known deterministic test records."""
    # Deterministic test fixture
    # Unit Price: 1000.0, Qty: 5, Discount: 20% (0.20)
    qty = 5
    unit_price = 1000.0
    discount_pct = 0.20

    gross_revenue = qty * unit_price
    discount_amount = gross_revenue * discount_pct
    net_revenue = gross_revenue - discount_amount

    assert gross_revenue == 5000.0, f"Gross revenue mismatch: expected 5000.0, got {gross_revenue}"
    assert discount_amount == 1000.0, f"Discount amount mismatch: expected 1000.0, got {discount_amount}"
    assert net_revenue == 4000.0, f"Net revenue mismatch: expected 4000.0, got {net_revenue}"


def test_tc_t_08_gross_profit_and_margin_percentage_formula():
    """TC-T-08: Verify gross profit margin and hurdle deficiency classification."""
    # Net Revenue: 4000.0, Base Cost (COGS): 2500.0, Freight: 500.0
    net_revenue = 4000.0
    total_cogs = 2500.0
    shipping_cost = 500.0

    gross_profit = net_revenue - total_cogs - shipping_cost
    gross_margin_pct = (gross_profit / net_revenue) * 100.0

    assert gross_profit == 1000.0, f"Gross profit mismatch: expected 1000.0, got {gross_profit}"
    assert gross_margin_pct == 25.0, f"Gross margin % mismatch: expected 25.0%, got {gross_margin_pct}%"

    # Hurdle check: 25.0% >= 15.0% -> Healthy
    margin_status = "Healthy" if gross_margin_pct >= 15.0 else "Margin Deficient"
    assert margin_status == "Healthy"

    # Deficient case: Net Revenue 4000, COGS 3200, Freight 500 -> Profit 300 -> Margin 7.5%
    def_profit = 4000.0 - 3200.0 - 500.0
    def_margin_pct = (def_profit / 4000.0) * 100.0
    def_status = "Healthy" if def_margin_pct >= 15.0 else "Margin Deficient"
    assert def_margin_pct == 7.5
    assert def_status == "Margin Deficient"


def test_tc_t_09_pareto_80_20_cumulative_calculation():
    """TC-T-09: Verify Pareto 80/20 category ranking and cumulative percentage math."""
    data = pd.DataFrame({
        "category": ["Electronics", "Apparel", "Home & Kitchen", "Office Supplies", "Health & Beauty"],
        "revenue": [50000.0, 30000.0, 10000.0, 7000.0, 3000.0]
    })
    total_rev = data["revenue"].sum()
    assert total_rev == 100000.0

    # Sort descending
    data = data.sort_values(by="revenue", ascending=False).reset_index(drop=True)
    data["cum_rev"] = data["revenue"].cumsum()
    data["cum_pct"] = (data["cum_rev"] / total_rev) * 100.0

    # Electronics (50%) + Apparel (30%) = exactly 80.0%
    assert data.loc[0, "cum_pct"] == 50.0
    assert data.loc[1, "cum_pct"] == 80.0
    
    # Classify Tier A (<= 80%) vs Tier B (> 80%)
    vital_few = data[data["cum_pct"] <= 80.0]["category"].tolist()
    assert vital_few == ["Electronics", "Apparel"], f"Expected Vital Few to be Electronics, Apparel; got {vital_few}"


def test_tc_t_10_quarterly_seasonality_index_calculation():
    """TC-T-10: Verify quarterly seasonality baseline indexing (baseline = 1.00)."""
    # 4 quarters sales: Q1: 200, Q2: 220, Q3: 210, Q4: 290
    q_sales = np.array([200.0, 220.0, 210.0, 290.0])
    mean_quarter = np.mean(q_sales)
    assert mean_quarter == 230.0

    seasonal_indices = q_sales / mean_quarter
    # Q4 Festive surge index: 290 / 230 ~ 1.26
    assert round(seasonal_indices[3], 2) == 1.26
    # Average of seasonal indices must equal 1.00
    assert round(np.mean(seasonal_indices), 2) == 1.00


def test_tc_t_11_statistical_dispersion_iqr_and_outliers():
    """TC-T-11: Verify 5-number summary, IQR, and Tukey outlier detection."""
    # Data with median=20, Q1=15, Q3=25 -> IQR=10. Upper boundary = 25 + 1.5*10 = 40
    # Include an extreme B2B outlier at 95.0
    values = np.array([10.0, 12.0, 14.0, 15.0, 18.0, 20.0, 22.0, 24.0, 25.0, 28.0, 30.0, 95.0])
    
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    upper_whisker = q3 + (1.5 * iqr)

    outliers = values[values > upper_whisker]
    assert 95.0 in outliers, "Failed to identify bulk B2B outlier using 1.5 * IQR rule"
    assert len(outliers) == 1, f"Expected 1 outlier, found {len(outliers)}"


def test_tc_t_12_inferential_hypothesis_testing_kruskal_and_anova():
    """TC-T-12: Verify statistical hypothesis testing functions (ANOVA / Kruskal-Wallis)."""
    # Create 3 distinct groups with significantly different means
    np.random.seed(42)
    group_north = np.random.normal(loc=25.0, scale=3.0, size=50)  # Healthy margins
    group_central = np.random.normal(loc=11.0, scale=3.0, size=50) # Deficient margins
    group_east = np.random.normal(loc=13.0, scale=3.0, size=50)    # Low margins

    # One-way ANOVA
    f_stat, p_val_anova = stats.f_oneway(group_north, group_central, group_east)
    assert p_val_anova < 0.001, f"Expected significant ANOVA p < 0.001, got {p_val_anova}"

    # Kruskal-Wallis Non-Parametric H-Test
    h_stat, p_val_kruskal = stats.kruskal(group_north, group_central, group_east)
    assert p_val_kruskal < 0.001, f"Expected significant Kruskal p < 0.001, got {p_val_kruskal}"
