# NOH Maternity Cashflow Dashboard
# Run: streamlit run app.py

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="NOH Maternity Cashflow", layout="wide")

# --- Auth ---
from auth import require_auth
if not require_auth():
    st.stop()

st.title("NOH Maternity Programme — 24-Month Cashflow Model")
st.caption("Disaggregated costs: antenatal midwifery · in-hospital midwifery · clinicians · board/facility · Rustenburg")

SCENARIO_COLORS = {
    "base":          "#599591",
    "optimistic":    "#2e6b68",
    "conservative":  "#f3bdc4",
    "high_cs_rate":  "#d4878f",
}


# --- Data loading: Supabase first, CSV fallback ---
def _get_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        try:
            url = st.secrets.get("SUPABASE_URL", url)
            key = st.secrets.get("SUPABASE_KEY", key)
        except Exception:
            pass
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            pass
    return None


@st.cache_data(ttl=300)
def load_scenarios():
    sb = _get_supabase()
    if sb:
        try:
            # Fetch scenario names
            scenarios = sb.table("scenarios").select("id, scenario_name").execute()
            id_map = {r["id"]: r["scenario_name"] for r in scenarios.data}

            # Fetch monthly data for noh-dashboard
            result = sb.table("scenario_monthly").select("*").eq("source_app", "noh-dashboard").execute()
            if result.data:
                df = pd.DataFrame(result.data)
                df["scenario"] = df["scenario_id"].map(id_map)
                return df
        except Exception:
            pass

    # CSV fallback
    out_dir = Path("outputs")
    path = out_dir / "2026-03-01_scenario_all.csv"
    if path.exists():
        return pd.read_csv(path)
    st.error("No data available. Check Supabase connection or local CSV files.")
    st.stop()


@st.cache_data(ttl=300)
def load_summary():
    sb = _get_supabase()
    if sb:
        try:
            scenarios = sb.table("scenarios").select("id, scenario_name").execute()
            id_map = {r["id"]: r["scenario_name"] for r in scenarios.data}

            result = sb.table("scenario_summary").select("*").eq("source_app", "noh-dashboard").execute()
            if result.data:
                df = pd.DataFrame(result.data)
                df["scenario"] = df["scenario_id"].map(id_map)
                return df
        except Exception:
            pass

    out_dir = Path("outputs")
    path = out_dir / "2026-03-01_scenario_summary.csv"
    if path.exists():
        return pd.read_csv(path)
    st.error("No summary data available.")
    st.stop()


df      = load_scenarios()
summary = load_summary()

# --- Sidebar ---
st.sidebar.header("Filters")
selected = st.sidebar.multiselect(
    "Scenarios",
    options=df["scenario"].unique().tolist(),
    default=df["scenario"].unique().tolist(),
)
df_f = df[df["scenario"].isin(selected)]

# --- KPI cards ---
st.subheader("Month 24 Summary")
if selected:
    cols = st.columns(len(selected))
    for i, scen in enumerate(selected):
        row = summary[summary["scenario"] == scen].iloc[0]
        cols[i].metric(
            label=scen.replace("_", " ").title(),
            value=f"R {row['cumulative_cash_m24']:,.0f}",
            delta=f"Net M24: R {row['net_cashflow_m24']:,.0f}",
        )

st.divider()

# --- Row 1: Cashflow ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Cumulative Cashflow")
    fig = px.line(
        df_f, x="month", y="cumulative_cash", color="scenario",
        color_discrete_map=SCENARIO_COLORS, markers=True,
        labels={"cumulative_cash": "Cumulative Cash (R)", "month": "Month"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="grey", annotation_text="Break-even")
    fig.update_layout(legend_title="Scenario", hovermode="x unified")
    st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("Net Cashflow per Month")
    fig2 = px.bar(
        df_f, x="month", y="net_cashflow", color="scenario",
        color_discrete_map=SCENARIO_COLORS, barmode="group",
        labels={"net_cashflow": "Net Cashflow (R)", "month": "Month"},
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="grey")
    fig2.update_layout(legend_title="Scenario", hovermode="x unified")
    st.plotly_chart(fig2, width='stretch')

st.divider()

# --- Row 2: Disaggregated cost waterfall (base scenario, month 24) ---
st.subheader("Cost Breakdown — Month 24")

if "base" in selected:
    base_m24 = df_f[(df_f["scenario"] == "base") & (df_f["month"] == 24)].iloc[0]
else:
    base_m24 = df_f[df_f["month"] == 24].iloc[0]

col3, col4 = st.columns(2)

with col3:
    st.markdown(f"**{base_m24['scenario'].replace('_',' ').title()} — Month 24 cost stack**")
    cost_labels = [
        "Antenatal Midwifery",
        "In-Hospital Midwifery",
        "MO Sessions",
        "MO Birth Fees",
        "Anaesthesia",
        "OB Pool",
        "Board / Facility",
    ]
    cost_values = [
        base_m24["antenatal_midwifery"],
        base_m24["inhosp_midwifery"],
        base_m24["mo_session_cost"],
        base_m24["mo_birth_cost"],
        base_m24["anaes_cost"],
        base_m24["ob_pool"],
        base_m24["board_facility"],
    ]
    fig3 = go.Figure(go.Bar(
        x=cost_values,
        y=cost_labels,
        orientation="h",
        marker_color=[
            "#f3bdc4", "#d4878f",
            "#599591", "#2e6b68", "#3a8582",
            "#a8d5d3",
            "#e8c07a",
        ],
        text=[f"R {v:,.0f}" for v in cost_values],
        textposition="outside",
    ))
    fig3.add_vline(x=base_m24["residual"], line_dash="dash", line_color="#599591",
                   annotation_text="Residual", annotation_position="top right")
    fig3.update_layout(xaxis_title="R", yaxis_title="", margin=dict(l=160))
    st.plotly_chart(fig3, width='stretch')

with col4:
    st.subheader("Midwifery vs Clinician vs Board")
    cost_df = df_f[["scenario", "month", "midwifery_costs", "clinician_costs", "board_facility"]].copy()
    cost_melt = cost_df.melt(
        id_vars=["scenario", "month"],
        value_vars=["midwifery_costs", "clinician_costs", "board_facility"],
        var_name="cost_type", value_name="amount"
    )
    cost_melt["cost_type"] = cost_melt["cost_type"].map({
        "midwifery_costs":  "Midwifery",
        "clinician_costs":  "Clinicians",
        "board_facility":   "Board / Facility",
    })
    fig4 = px.area(
        cost_melt[cost_melt["scenario"].isin(selected)],
        x="month", y="amount", color="cost_type",
        facet_col="scenario", facet_col_wrap=2,
        color_discrete_map={
            "Midwifery":        "#f3bdc4",
            "Clinicians":       "#599591",
            "Board / Facility": "#e8c07a",
        },
        labels={"amount": "R", "month": "Month", "cost_type": "Cost"},
    )
    fig4.update_layout(hovermode="x unified")
    st.plotly_chart(fig4, width='stretch')

st.divider()

# --- Row 3: Revenue vs Total Costs ---
col5, col6 = st.columns(2)

with col5:
    st.subheader("Residual vs Total Costs")
    fig5 = px.line(
        df_f, x="month", y=["residual", "total_costs"], color="scenario",
        color_discrete_map=SCENARIO_COLORS,
        labels={"value": "R", "month": "Month", "variable": ""},
        line_dash="variable",
    )
    fig5.update_layout(legend_title="Scenario / Line", hovermode="x unified")
    st.plotly_chart(fig5, width='stretch')

with col6:
    st.subheader("Births by Type — Base Scenario")
    base_df = df[df["scenario"] == "base"].copy()
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(name="NVD (midwife-only)", x=base_df["month"],
                          y=(base_df["nvd_cases"] * (1 - 0.175)).round(1),
                          marker_color="#f3bdc4"))
    fig6.add_trace(go.Bar(name="NVD (MO-assisted)", x=base_df["month"],
                          y=(base_df["nvd_cases"] * 0.175).round(1),
                          marker_color="#599591"))
    fig6.add_trace(go.Bar(name="CS", x=base_df["month"],
                          y=base_df["cs_cases"].round(1),
                          marker_color="#2e6b68"))
    fig6.update_layout(barmode="stack", xaxis_title="Month", yaxis_title="Cases",
                       legend_title="Birth Type", hovermode="x unified")
    st.plotly_chart(fig6, width='stretch')

st.divider()

# --- Summary table ---
st.subheader("Scenario Comparison Table")
fmt = {
    "total_receipts_m24":   "R {:,.0f}",
    "midwifery_costs_m24":  "R {:,.0f}",
    "clinician_costs_m24":  "R {:,.0f}",
    "board_facility_m24":   "R {:,.0f}",
    "total_costs_m24":      "R {:,.0f}",
    "net_cashflow_m12":     "R {:,.0f}",
    "net_cashflow_m24":     "R {:,.0f}",
    "cumulative_cash_m24":  "R {:,.0f}",
}
st.dataframe(
    summary[summary["scenario"].isin(selected)].set_index("scenario").style.format(fmt),
    width='stretch',
)

# --- Raw data ---
with st.expander("Raw scenario data"):
    st.dataframe(df_f, width='stretch')
