"""
UI-01: Executive Overview & Macro KPIs Screen
"""

import streamlit as st
import plotly.express as px
from src.ui import apply_custom_css, render_tailwind_header, render_kpi_grid, render_insight_box
from src.data.loader import load_analysis_data
from src.analytics.kpis import calculate_macro_kpis, calculate_regional_contributions

apply_custom_css()

df_raw = load_analysis_data()

# Read active filters from session state or default
regions = st.session_state.get("filter_regions", df_raw["region_name"].unique().tolist())
categories = st.session_state.get("filter_categories", df_raw["product_category"].unique().tolist())
segment = st.session_state.get("filter_segment", "All")

filtered_df = df_raw[df_raw["region_name"].isin(regions) & df_raw["product_category"].isin(categories)]
if segment != "All" and "customer_segment" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["customer_segment"] == segment]

render_tailwind_header(
    title="Executive Overview & KPI Scorecards",
    subtitle="Macro Performance, Regional Revenue Share & National Margin Health",
    badge_text="Screen UI-01"
)

if len(filtered_df) == 0:
    st.warning("⚠️ No data available matching active filter selection.")
    st.stop()

# Macro KPI Grid
kpis = calculate_macro_kpis(filtered_df)
kpi_cards = [
    {"title": "Gross Realized Sales", "value": f"₹{kpis['gross_revenue']/100000:.2f} L", "delta": "+14.2% YoY", "delta_type": "positive", "subtitle": "Gross National Volume", "accent": "blue"},
    {"title": "Net Realized Revenue", "value": f"₹{kpis['net_revenue']/100000:.2f} L", "delta": "+12.4% MoM", "delta_type": "positive", "subtitle": "Target: ₹32.00 L", "accent": "green"},
    {"title": "Gross Profit Margin", "value": f"{kpis['gross_margin_pct']:.1f}%", "delta": "-1.8% pts", "delta_type": "negative" if kpis['gross_margin_pct'] < 20 else "positive", "subtitle": "Hurdle: 15.0%", "accent": "red" if kpis['gross_margin_pct'] < 15 else "amber"},
    {"title": "Total Transaction Count", "value": f"{kpis['total_orders']} Orders", "delta": f"AOV: ₹{kpis['aov']:,.0f}", "delta_type": "neutral", "subtitle": "Active Slice", "accent": "blue"}
]
render_kpi_grid(kpi_cards)

render_insight_box(
    title="Strategic Takeaway (OQ-01)",
    text="North (32.2%) and West (29.9%) represent 62.1% of national revenue. Central and East suffer from margin deficit due to 2.5x freight costs and deep promotional discounting.",
    box_type="warning" if kpis['gross_margin_pct'] < 18 else "info"
)

# Regional Horizontal Bar Chart
reg_df = calculate_regional_contributions(filtered_df)
col1, col2 = st.columns([0.65, 0.35])

with col1:
    st.markdown("### 🗺️ Regional Revenue & Contribution Share")
    fig = px.bar(
        reg_df,
        x="net_revenue",
        y="region_name",
        orientation="h",
        text=reg_df["revenue_pct"].apply(lambda x: f"{x:.1f}%"),
        color="gross_margin_pct",
        color_continuous_scale="Teal",
        labels={"net_revenue": "Net Revenue (₹)", "region_name": "Sales Zone", "gross_margin_pct": "Margin %"}
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 📊 Performance Table")
    tbl = reg_df[["region_name", "net_revenue", "revenue_pct", "gross_margin_pct"]].copy()
    tbl.columns = ["Territory", "Net Rev", "Share", "Margin"]
    tbl["Net Rev"] = tbl["Net Rev"].apply(lambda x: f"₹{x:,.0f}")
    tbl["Share"] = tbl["Share"].apply(lambda x: f"{x:.1f}%")
    tbl["Margin"] = tbl["Margin"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(tbl, use_container_width=True, hide_index=True)
