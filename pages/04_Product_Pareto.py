"""
UI-04: Product Category Pareto Analysis & Statistical Dispersion
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.ui import apply_custom_css, render_tailwind_header, render_insight_box
from src.data.loader import load_analysis_data
from src.analytics.pareto import calculate_category_pareto
from src.analytics.statistics import calculate_ticket_dispersion

apply_custom_css()

df_raw = load_analysis_data()
regions = st.session_state.get("filter_regions", df_raw["region_name"].unique().tolist())
filtered_df = df_raw[df_raw["region_name"].isin(regions)]

render_tailwind_header(
    title="Product Category Pareto (80/20) & Ticket Size IQR",
    subtitle="Vital Few SKUs Identification & Order Size Dispersion Analysis",
    badge_text="Screen UI-04"
)

if len(filtered_df) == 0:
    st.warning("⚠️ No records matching active filters.")
    st.stop()

# Dual-Axis Pareto Chart (OQ-04)
st.markdown("### 📦 Product Category Pareto Analysis (80/20 Distribution)")
pareto_df = calculate_category_pareto(filtered_df)

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(
    x=pareto_df["product_category"],
    y=pareto_df["net_revenue"],
    name="Net Revenue (₹)",
    marker_color="#2563EB",
    yaxis="y1"
))
fig_pareto.add_trace(go.Scatter(
    x=pareto_df["product_category"],
    y=pareto_df["cum_pct"],
    name="Cumulative Share %",
    mode="lines+markers",
    line=dict(color="#E11D48", width=3),
    yaxis="y2"
))
# 80% Cutoff Line
fig_pareto.add_hline(y=80.0, line_dash="dash", line_color="#D97706", yref="y2", annotation_text="80% Vital Few Hurdle")

fig_pareto.update_layout(
    yaxis=dict(title="Net Realized Revenue (₹)", side="left"),
    yaxis2=dict(title="Cumulative Revenue %", overlaying="y", side="right", range=[0, 105]),
    height=380,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_pareto, use_container_width=True)

# Statistical Ticket Size Boxplot (OQ-06)
st.markdown("### 📊 Regional Order Ticket Size Statistical Dispersion (IQR & Outliers)")
fig_box = px.box(
    filtered_df,
    x="region_name",
    y="net_revenue",
    color="region_name",
    points="outliers",
    labels={"region_name": "Sales Zone", "net_revenue": "Order Ticket Size (₹)"}
)
fig_box.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_box, use_container_width=True)

render_insight_box(
    title="Pareto & Ticket Size Findings",
    text="Electronics and Home & Kitchen represent the 'Vital Few' (driving ~80% of revenue in North and West). Isolated points beyond ₹90k in boxplots reflect B2B corporate bulk orders (quantity 95), while typical consumer ticket median sits at ₹16,500.",
    box_type="info"
)
