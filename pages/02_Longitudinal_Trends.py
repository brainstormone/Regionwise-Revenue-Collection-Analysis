"""
UI-02: Longitudinal Trends & Seasonality Decomposition Screen
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ui import apply_custom_css, render_tailwind_header, render_insight_box
from src.data.loader import load_analysis_data
from src.analytics.statistics import calculate_quarterly_seasonality_index

apply_custom_css()

df_raw = load_analysis_data()
regions = st.session_state.get("filter_regions", df_raw["region_name"].unique().tolist())
filtered_df = df_raw[df_raw["region_name"].isin(regions)]

render_tailwind_header(
    title="Longitudinal Trends & Festive Seasonality",
    subtitle="Month-over-Month Growth Trajectories & Q4 Festive Spike Decomposition",
    badge_text="Screen UI-02"
)

if len(filtered_df) == 0:
    st.warning("⚠️ No records matching active filters.")
    st.stop()

# Time Granularity Toggle
granularity = st.radio("Time Aggregation:", options=["Monthly", "Quarterly"], horizontal=True)

temp_df = filtered_df.copy()
temp_df["year_month"] = temp_df["order_date"].dt.to_period("M").astype(str)
temp_df["quarter"] = "Q" + temp_df["order_date"].dt.quarter.astype(str) + " 2024"

group_col = "year_month" if granularity == "Monthly" else "quarter"
trend_data = temp_df.groupby(group_col)["net_revenue"].sum().reset_index()
trend_data["mom_pct"] = trend_data["net_revenue"].pct_change() * 100.0

# Dual-Axis Plotly Chart
fig = go.Figure()
fig.add_trace(go.Bar(
    x=trend_data[group_col],
    y=trend_data["net_revenue"],
    name="Net Revenue (₹)",
    marker_color="#2563EB",
    yaxis="y1"
))
fig.add_trace(go.Scatter(
    x=trend_data[group_col],
    y=trend_data["mom_pct"],
    name=f"{'MoM' if granularity == 'Monthly' else 'QoQ'} % Change",
    mode="lines+markers+text",
    text=trend_data["mom_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else ""),
    textposition="top center",
    line=dict(color="#E11D48", width=3),
    yaxis="y2"
))
fig.update_layout(
    title=f"Net Revenue Trajectory & {granularity} Growth Rate",
    yaxis=dict(title="Net Realized Revenue (₹)", side="left"),
    yaxis2=dict(title=f"{'MoM' if granularity == 'Monthly' else 'QoQ'} % Growth", overlaying="y", side="right"),
    height=400,
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# Seasonality Index Heatmap (OQ-10)
st.markdown("### 🗓️ Regional Seasonality Heatmap (Baseline = 1.00)")
national_q, regional_matrix = calculate_quarterly_seasonality_index(filtered_df)

if not regional_matrix.empty:
    fig_heat = px.imshow(
        regional_matrix,
        text_auto=".2f",
        color_continuous_scale="Viridis",
        aspect="auto",
        labels=dict(x="Calendar Quarter", y="Territory", color="Seasonal Index")
    )
    fig_heat.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

render_insight_box(
    title="Seasonal Dynamics (OQ-10)",
    text="Q4 festive seasonality index surges to ~1.30 (+30% above baseline) driven by Diwali and year-end corporate buying. Supply chain buffers in North and West must be reinforced 6 weeks prior to Q4.",
    box_type="info"
)
