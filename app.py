# NOH Maternity Team Dashboard — Clinical Operations
# Run: streamlit run app.py

import os
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, timedelta

from constants import (
    SITES, DELIVERY_MODE_LABELS, BABY_OUTCOME_LABELS,
    MATERNAL_EVENT_LABELS, WARD_LABELS, SAC_RATINGS,
    AUDIT_TYPE_LABELS, SOP_REFERENCES,
    NOH_TEAL, NOH_TEAL_DARK, NOH_PINK_LIGHT, NOH_PINK_DARK,
    NOH_GOLD, RAG_GREEN, RAG_AMBER, RAG_RED, RAG_BG,
)
from insist import (
    INSIST_PRIMARY_CAUSES, INSIST_FINAL_CAUSES, AVOIDABLE_FACTORS,
    is_perinatal_death, is_stillbirth, is_neonatal_death,
)
from kpi_engine import compute_birth_kpis, get_targets_map, rag_color, rag_status
import data_access as db
import forms

st.set_page_config(
    page_title="NOH Maternity Dashboard",
    page_icon="🏥",
    layout="wide",
)

# --- Auth ---
from auth import require_auth
if not require_auth():
    st.stop()

user_email = st.session_state.get("user_email", "unknown")


# ===== SIDEBAR =====
st.sidebar.title("NOH Maternity")
st.sidebar.caption("Clinical Team Dashboard")

# Site selector
site_options = {sk: si["label"] for sk, si in SITES.items()}
selected_site = st.sidebar.selectbox(
    "Site", options=list(site_options.keys()),
    format_func=lambda s: site_options[s],
)
site_label = SITES[selected_site]["label"]

# Date range
st.sidebar.header("Date Range")
range_option = st.sidebar.selectbox(
    "Period",
    ["This month", "Today", "This week", "This quarter", "Last 12 months", "Custom"],
)

today = date.today()
if range_option == "Today":
    date_from = date_to = today
elif range_option == "This week":
    date_from = today - timedelta(days=today.weekday())
    date_to = today
elif range_option == "This month":
    date_from = today.replace(day=1)
    date_to = today
elif range_option == "This quarter":
    q_month = ((today.month - 1) // 3) * 3 + 1
    date_from = today.replace(month=q_month, day=1)
    date_to = today
elif range_option == "Last 12 months":
    date_from = today - timedelta(days=365)
    date_to = today
else:
    date_from = st.sidebar.date_input("From", value=today.replace(day=1))
    date_to = st.sidebar.date_input("To", value=today)

st.sidebar.caption(f"{date_from} to {date_to}")

# Refresh
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()


# ===== LOAD DATA =====
births_raw = db.get_births(selected_site, date_from, date_to)
births_df = pd.DataFrame(births_raw) if births_raw else pd.DataFrame()

events_raw = db.get_maternal_events(selected_site, date_from, date_to)
events_df = pd.DataFrame(events_raw) if events_raw else pd.DataFrame()

census_raw = db.get_ward_census(selected_site, today)
census_df = pd.DataFrame(census_raw) if census_raw else pd.DataFrame()

incidents_raw = db.get_incidents(selected_site, date_from, date_to)
incidents_df = pd.DataFrame(incidents_raw) if incidents_raw else pd.DataFrame()

# KPI targets
targets_raw = db.get_kpi_targets(selected_site)
targets_df = pd.DataFrame(targets_raw) if targets_raw else pd.DataFrame()
targets_map = get_targets_map(targets_df if not targets_df.empty else None)

# Compute KPIs
kpis = compute_birth_kpis(births_df, targets_map) if not births_df.empty else []
kpi_map = {k["code"]: k for k in kpis}

n_births = len(births_df)


# ===== HEADER =====
st.title(f"NOH Maternity Dashboard - {site_label}")
st.caption(f"Period: {date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')} | {n_births} births recorded")


# ===== HELPER =====
def metric_with_rag(col, label, kpi_code, fallback_val=None, suffix=""):
    """Display a metric card with RAG colouring."""
    k = kpi_map.get(kpi_code)
    if k and k["value"] is not None:
        val = k["value"]
        rag = k["rag"]
        color = rag_color(rag)
        bg = RAG_BG.get(rag, "#f5f5f5")
        col.markdown(
            f'<div style="background:{bg}; border-left:4px solid {color}; padding:12px; border-radius:6px; margin-bottom:8px;">'
            f'<div style="font-size:0.8em; color:#666;">{label}</div>'
            f'<div style="font-size:1.6em; font-weight:bold; color:{color};">{val}{suffix}</div>'
            f'<div style="font-size:0.7em; color:#999;">{k.get("source", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        val = fallback_val if fallback_val is not None else "-"
        col.markdown(
            f'<div style="background:#f5f5f5; border-left:4px solid #9e9e9e; padding:12px; border-radius:6px; margin-bottom:8px;">'
            f'<div style="font-size:0.8em; color:#666;">{label}</div>'
            f'<div style="font-size:1.6em; font-weight:bold; color:#333;">{val}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ===== TABS =====
tabs = st.tabs([
    "Morning Huddle",
    "Birth Register",
    "INSIST Outcomes",
    "Maternal Safety",
    "Quality Scorecard",
    "Patient Flow",
    "Staff & Training",
    "Governance",
    "Data Entry",
])


# ===== TAB 1: MORNING HUDDLE =====
with tabs[0]:
    st.subheader("At a Glance")

    # Row 1: KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Births (period)", n_births)
    metric_with_rag(c2, "CS Rate", "cs_rate", suffix="%")
    metric_with_rag(c3, "Perinatal Mortality", "pnmr", suffix="/1000")
    metric_with_rag(c4, "PPH Rate", "pph_rate", suffix="%")
    metric_with_rag(c5, "Skin-to-Skin", "skin_to_skin_rate", suffix="%")
    metric_with_rag(c6, "Partograph", "partograph_rate", suffix="%")

    # Open incidents
    open_incidents = len(incidents_df[incidents_df["status"] == "open"]) if not incidents_df.empty and "status" in incidents_df.columns else 0
    if open_incidents > 0:
        st.warning(f"**{open_incidents} open incident(s)** require attention.")

    st.divider()

    # Row 2: Recent births
    st.subheader("Recent Births")
    if not births_df.empty:
        display_cols = ["birth_date", "birth_time", "delivery_mode", "baby_outcome",
                        "birth_weight_g", "apgar_5min", "ebl_ml"]
        available = [c for c in display_cols if c in births_df.columns]
        recent = births_df.head(10)[available].copy()
        if "delivery_mode" in recent.columns:
            recent["delivery_mode"] = recent["delivery_mode"].map(DELIVERY_MODE_LABELS)
        if "baby_outcome" in recent.columns:
            recent["baby_outcome"] = recent["baby_outcome"].map(BABY_OUTCOME_LABELS)
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No births recorded for this period. Use the Data Entry tab to log births.")

    st.divider()

    # Row 3: Ward census
    st.subheader("Ward Census (Today)")
    if not census_df.empty:
        for _, row in census_df.iterrows():
            ward_name = WARD_LABELS.get(row.get("ward", ""), row.get("ward", ""))
            patients = row.get("patients_count", 0)
            capacity = row.get("bed_capacity", 1)
            occupancy = round(patients / capacity * 100) if capacity > 0 else 0
            rag = "green" if occupancy <= 80 else ("amber" if occupancy <= 95 else "red")
            color = rag_color(rag)
            st.markdown(
                f"**{ward_name}**: {patients}/{capacity} beds "
                f'(<span style="color:{color}; font-weight:bold;">{occupancy}%</span>)',
                unsafe_allow_html=True,
            )
    else:
        st.info("No ward census recorded today. Use Data Entry > Ward Census.")

    # Births trend (daily for the period)
    if not births_df.empty and "birth_date" in births_df.columns:
        st.divider()
        st.subheader("Daily Birth Trend")
        daily = births_df.groupby("birth_date").size().reset_index(name="births")
        fig_daily = px.bar(
            daily, x="birth_date", y="births",
            labels={"birth_date": "Date", "births": "Births"},
            color_discrete_sequence=[NOH_TEAL],
        )
        fig_daily.update_layout(hovermode="x unified", height=250)
        st.plotly_chart(fig_daily, use_container_width=True)


# ===== TAB 2: BIRTH REGISTER =====
with tabs[1]:
    st.subheader("Birth Register")
    if not births_df.empty:
        # Delivery mode breakdown
        col_a, col_b = st.columns(2)
        with col_a:
            mode_counts = births_df["delivery_mode"].value_counts().reset_index()
            mode_counts.columns = ["mode", "count"]
            mode_counts["mode_label"] = mode_counts["mode"].map(DELIVERY_MODE_LABELS)
            fig_mode = px.pie(
                mode_counts, values="count", names="mode_label",
                color_discrete_sequence=[NOH_TEAL, NOH_TEAL_DARK, NOH_PINK_LIGHT, NOH_PINK_DARK, NOH_GOLD],
                title="Delivery Mode Distribution",
            )
            st.plotly_chart(fig_mode, use_container_width=True)

        with col_b:
            if "birth_weight_g" in births_df.columns:
                fig_bw = px.histogram(
                    births_df, x="birth_weight_g", nbins=20,
                    title="Birth Weight Distribution",
                    labels={"birth_weight_g": "Birth Weight (g)"},
                    color_discrete_sequence=[NOH_TEAL],
                )
                st.plotly_chart(fig_bw, use_container_width=True)

        st.divider()

        # Full register table
        display = births_df.copy()
        if "delivery_mode" in display.columns:
            display["delivery_mode"] = display["delivery_mode"].map(DELIVERY_MODE_LABELS)
        if "baby_outcome" in display.columns:
            display["baby_outcome"] = display["baby_outcome"].map(BABY_OUTCOME_LABELS)
        show_cols = [c for c in [
            "birth_date", "birth_time", "patient_id", "delivery_mode",
            "gestational_age_weeks", "birth_weight_g", "apgar_5min",
            "ebl_ml", "baby_outcome", "skin_to_skin_1hr", "pph",
        ] if c in display.columns]
        st.dataframe(display[show_cols], use_container_width=True, hide_index=True)

        # CSV download
        csv = display[show_cols].to_csv(index=False)
        st.download_button("Download birth register (CSV)", csv,
                           file_name=f"noh_{selected_site}_births_{date_from}_{date_to}.csv",
                           mime="text/csv")
    else:
        st.info("No births recorded for this period.")


# ===== TAB 3: INSIST OUTCOMES =====
with tabs[2]:
    st.subheader("INSIST Perinatal Outcomes")

    if not births_df.empty and "baby_outcome" in births_df.columns:
        # Headline indicators
        total_births_insist = len(births_df)
        live_births = len(births_df[births_df["baby_outcome"].isin(["live_well", "live_nicu"])])
        stillbirths = len(births_df[births_df["baby_outcome"].isin(["stillbirth_macerated", "stillbirth_fresh"])])
        fresh_sb = len(births_df[births_df["baby_outcome"] == "stillbirth_fresh"])
        mac_sb = len(births_df[births_df["baby_outcome"] == "stillbirth_macerated"])
        ennd = len(births_df[births_df["baby_outcome"] == "early_nnd"])
        lnnd = len(births_df[births_df["baby_outcome"] == "late_nnd"])
        total_deaths = stillbirths + ennd + lnnd

        c1, c2, c3, c4 = st.columns(4)
        metric_with_rag(c1, "PNMR (per 1000)", "pnmr")
        metric_with_rag(c2, "Stillbirth Rate", "sbr")
        metric_with_rag(c3, "Fresh SB Rate", "fresh_sbr")
        metric_with_rag(c4, "ENND Rate", "enndr")

        st.divider()

        col_i1, col_i2 = st.columns(2)

        with col_i1:
            st.subheader("Outcomes Summary")
            st.markdown(f"""
            | Outcome | Count |
            |---------|-------|
            | Total births | {total_births_insist} |
            | Live births (well) | {len(births_df[births_df['baby_outcome'] == 'live_well'])} |
            | Live births (NICU) | {len(births_df[births_df['baby_outcome'] == 'live_nicu'])} |
            | Macerated stillbirths | {mac_sb} |
            | Fresh stillbirths | {fresh_sb} |
            | Early neonatal deaths | {ennd} |
            | Late neonatal deaths | {lnnd} |
            | **Total perinatal deaths** | **{total_deaths}** |
            """)

        with col_i2:
            # INSIST classification pie (if any deaths with classification)
            death_records = births_df[births_df["baby_outcome"].isin(
                ["stillbirth_macerated", "stillbirth_fresh", "early_nnd", "late_nnd"]
            )]
            if not death_records.empty and "insist_primary_cause" in death_records.columns:
                classified = death_records[death_records["insist_primary_cause"].notna()]
                if not classified.empty:
                    cause_counts = classified["insist_primary_cause"].value_counts().reset_index()
                    cause_counts.columns = ["cause", "count"]
                    cause_counts["cause_label"] = cause_counts["cause"].map(INSIST_PRIMARY_CAUSES)
                    fig_insist = px.pie(
                        cause_counts, values="count", names="cause_label",
                        title="INSIST Primary Obstetric Cause",
                    )
                    st.plotly_chart(fig_insist, use_container_width=True)
                else:
                    st.info("No INSIST classifications recorded for perinatal deaths.")
            elif total_deaths > 0:
                st.warning(f"{total_deaths} perinatal death(s) not yet classified with INSIST codes.")
            else:
                st.success("No perinatal deaths in this period.")

        # Perinatal death list
        if total_deaths > 0:
            st.divider()
            st.subheader("Perinatal Death Register")
            death_display = death_records.copy()
            show_death_cols = [c for c in [
                "birth_date", "baby_outcome", "gestational_age_weeks",
                "birth_weight_g", "delivery_mode", "insist_primary_cause",
                "insist_final_cause", "insist_avoidable_factor",
            ] if c in death_display.columns]
            if "baby_outcome" in death_display.columns:
                death_display["baby_outcome"] = death_display["baby_outcome"].map(BABY_OUTCOME_LABELS)
            if "insist_primary_cause" in death_display.columns:
                death_display["insist_primary_cause"] = death_display["insist_primary_cause"].map(INSIST_PRIMARY_CAUSES)
            if "insist_avoidable_factor" in death_display.columns:
                death_display["insist_avoidable_factor"] = death_display["insist_avoidable_factor"].map(AVOIDABLE_FACTORS)
            st.dataframe(death_display[show_death_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No birth data available for INSIST analysis.")


# ===== TAB 4: MATERNAL SAFETY =====
with tabs[3]:
    st.subheader("Maternal Safety")

    if not births_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        metric_with_rag(c1, "PPH Rate", "pph_rate", suffix="%")
        metric_with_rag(c2, "Severe PPH Rate", "severe_pph_rate", suffix="%")

        # Maternal events counts
        n_events = len(events_df)
        c3.metric("Maternal Events", n_events)
        icu_count = len(events_df[events_df["event_type"] == "icu_admission"]) if not events_df.empty and "event_type" in events_df.columns else 0
        c4.metric("ICU Admissions", icu_count)

    if not events_df.empty:
        st.divider()
        st.subheader("Maternal Event Log")
        display_events = events_df.copy()
        if "event_type" in display_events.columns:
            display_events["event_type"] = display_events["event_type"].map(MATERNAL_EVENT_LABELS)
        show_cols = [c for c in ["event_date", "event_type", "severity", "ebl_ml",
                                  "blood_units_transfused", "icu_days", "description"]
                     if c in display_events.columns]
        st.dataframe(display_events[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No maternal events recorded for this period.")


# ===== TAB 5: QUALITY SCORECARD =====
with tabs[4]:
    st.subheader("Quality Scorecard")

    if kpis:
        # Group KPIs for display
        groups = {
            "Delivery Practice": ["cs_rate", "emergency_cs_rate", "episiotomy_rate", "tear_3_4_rate"],
            "Newborn Care": ["skin_to_skin_rate", "bf_initiation_rate", "apgar_low_rate"],
            "Perinatal Outcomes": ["pnmr", "sbr", "fresh_sbr", "enndr"],
            "Maternal Safety": ["pph_rate", "severe_pph_rate"],
            "PMTCT": ["pmtct_testing_rate"],
            "Documentation": ["partograph_rate"],
        }

        for group_name, codes in groups.items():
            st.markdown(f"**{group_name}**")
            group_kpis = [k for k in kpis if k["code"] in codes]
            if group_kpis:
                for k in group_kpis:
                    color = rag_color(k["rag"])
                    bg = RAG_BG.get(k["rag"], "#f5f5f5")
                    val_str = f"{k['value']}{k['unit']}" if k["value"] is not None else "N/A"
                    st.markdown(
                        f'<div style="display:flex; align-items:center; background:{bg}; '
                        f'border-left:4px solid {color}; padding:8px 12px; margin:4px 0; border-radius:4px;">'
                        f'<div style="flex:1; font-weight:bold;">{k["name"]}</div>'
                        f'<div style="width:100px; text-align:right; font-size:1.2em; color:{color}; font-weight:bold;">{val_str}</div>'
                        f'<div style="width:120px; text-align:right; font-size:0.8em; color:#999;">{k.get("source", "")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown("")
    else:
        st.info("No data available to compute quality scorecard. Log births to see KPIs.")


# ===== TAB 6: PATIENT FLOW =====
with tabs[5]:
    st.subheader("Patient Flow")

    # Ward occupancy gauges
    if not census_df.empty:
        ward_cols = st.columns(len(census_df))
        for i, (_, row) in enumerate(census_df.iterrows()):
            ward_name = WARD_LABELS.get(row.get("ward", ""), row.get("ward", ""))
            patients = row.get("patients_count", 0)
            capacity = row.get("bed_capacity", 1)
            occupancy = round(patients / capacity * 100) if capacity > 0 else 0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=occupancy,
                title={"text": ward_name, "font": {"size": 12}},
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": NOH_TEAL},
                    "steps": [
                        {"range": [0, 80], "color": "#e8f5e9"},
                        {"range": [80, 95], "color": "#fff8e1"},
                        {"range": [95, 100], "color": "#ffebee"},
                    ],
                },
            ))
            fig_gauge.update_layout(height=180, margin=dict(t=40, b=10, l=20, r=20))
            ward_cols[i].plotly_chart(fig_gauge, use_container_width=True)

        st.divider()

        # Midwife ratios
        labour_census = census_df[census_df["ward"] == "labour"] if "ward" in census_df.columns else pd.DataFrame()
        if not labour_census.empty:
            lc = labour_census.iloc[0]
            mw = lc.get("midwives_on_duty", 0)
            pts = lc.get("patients_count", 0)
            ratio_str = f"1:{pts/mw:.1f}" if mw > 0 else "No midwives recorded"
            st.metric("Labour Ward Midwife-to-Patient Ratio", ratio_str)
    else:
        st.info("No ward census data for today. Use Data Entry > Ward Census.")

    st.divider()

    # Antenatal pipeline
    st.subheader("Antenatal Bookings Pipeline")
    bookings_raw = db.get_antenatal_bookings(selected_site, active_only=True)
    if bookings_raw:
        bookings_df = pd.DataFrame(bookings_raw)
        if "edd" in bookings_df.columns:
            bookings_df["edd"] = pd.to_datetime(bookings_df["edd"])
            bookings_df["week"] = bookings_df["edd"].dt.isocalendar().week
            upcoming = bookings_df[bookings_df["edd"] >= pd.Timestamp(today)]
            next_4w = upcoming[upcoming["edd"] <= pd.Timestamp(today + timedelta(weeks=4))]
            st.metric("Expected deliveries (next 4 weeks)", len(next_4w))

            if not next_4w.empty:
                weekly = next_4w.groupby("week").size().reset_index(name="expected")
                fig_pipe = px.bar(
                    weekly, x="week", y="expected",
                    labels={"week": "ISO Week", "expected": "Expected Deliveries"},
                    color_discrete_sequence=[NOH_TEAL],
                    title="Expected Deliveries by Week",
                )
                st.plotly_chart(fig_pipe, use_container_width=True)
    else:
        st.info("No active antenatal bookings.")


# ===== TAB 7: STAFF & TRAINING =====
with tabs[6]:
    st.subheader("Staff & Training")

    training_raw = db.get_staff_training(selected_site, date_from, date_to)
    if training_raw:
        training_df = pd.DataFrame(training_raw)

        # Overall compliance
        if "passed" in training_df.columns:
            pass_rate = round(training_df["passed"].mean() * 100, 1)
            st.metric("Training Pass Rate", f"{pass_rate}%")

        st.divider()

        # Competency by SOP
        if "sop_reference" in training_df.columns:
            st.subheader("Competency by SOP")
            sop_data = training_df[training_df["sop_reference"].notna()]
            if not sop_data.empty:
                sop_summary = sop_data.groupby("sop_reference").agg(
                    assessed=("id", "count"),
                    passed=("passed", "sum"),
                ).reset_index()
                sop_summary["pass_rate"] = (sop_summary["passed"] / sop_summary["assessed"] * 100).round(1)
                sop_summary["sop_name"] = sop_summary["sop_reference"].map(SOP_REFERENCES)
                st.dataframe(
                    sop_summary[["sop_reference", "sop_name", "assessed", "passed", "pass_rate"]],
                    use_container_width=True, hide_index=True,
                )

        st.divider()

        # Training log
        st.subheader("Training Log")
        show_cols = [c for c in ["training_date", "staff_name", "staff_role",
                                  "training_type", "sop_reference", "score_pct", "passed"]
                     if c in training_df.columns]
        st.dataframe(training_df[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No training records for this period.")


# ===== TAB 8: GOVERNANCE =====
with tabs[7]:
    st.subheader("Governance")

    # Incidents
    if not incidents_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        open_inc = incidents_df[incidents_df["status"] == "open"] if "status" in incidents_df.columns else pd.DataFrame()
        c1.metric("Open Incidents", len(open_inc))

        sac_12 = open_inc[open_inc["sac_rating"].isin([1, 2])] if "sac_rating" in open_inc.columns else pd.DataFrame()
        if len(sac_12) > 0:
            c2.metric("SAC 1-2 Open", len(sac_12), delta="URGENT", delta_color="inverse")
        else:
            c2.metric("SAC 1-2 Open", 0)

        overdue = pd.DataFrame()
        if "investigation_due_date" in open_inc.columns:
            open_inc_copy = open_inc.copy()
            open_inc_copy["investigation_due_date"] = pd.to_datetime(open_inc_copy["investigation_due_date"])
            overdue = open_inc_copy[open_inc_copy["investigation_due_date"] < pd.Timestamp(today)]
        c3.metric("Overdue Investigations", len(overdue))

        c4.metric("Total Incidents (period)", len(incidents_df))

        st.divider()
        st.subheader("Incident Log")
        display_inc = incidents_df.copy()
        show_cols = [c for c in ["incident_date", "sac_rating", "category", "status",
                                  "patient_harm", "description"]
                     if c in display_inc.columns]
        st.dataframe(display_inc[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No incidents recorded for this period.")

    st.divider()

    # Audit scores
    st.subheader("Clinical Audits")
    audit_raw = db.get_audit_scores(selected_site, date_from, date_to)
    if audit_raw:
        audit_df = pd.DataFrame(audit_raw)
        display_audit = audit_df.copy()
        if "audit_type" in display_audit.columns:
            display_audit["audit_type"] = display_audit["audit_type"].map(AUDIT_TYPE_LABELS)
        show_cols = [c for c in ["audit_date", "audit_type", "score_pct", "sample_size", "auditor"]
                     if c in display_audit.columns]
        st.dataframe(display_audit[show_cols], use_container_width=True, hide_index=True)

        # Audit score trend
        if "audit_date" in audit_df.columns and "score_pct" in audit_df.columns:
            fig_audit = px.line(
                audit_df.sort_values("audit_date"),
                x="audit_date", y="score_pct", color="audit_type" if "audit_type" in audit_df.columns else None,
                title="Audit Score Trend",
                labels={"audit_date": "Date", "score_pct": "Score (%)"},
            )
            fig_audit.add_hline(y=80, line_dash="dash", line_color=RAG_GREEN, annotation_text="Target 80%")
            fig_audit.add_hline(y=60, line_dash="dash", line_color=RAG_AMBER, annotation_text="Minimum 60%")
            st.plotly_chart(fig_audit, use_container_width=True)
    else:
        st.info("No audit records for this period.")


# ===== TAB 9: DATA ENTRY =====
with tabs[8]:
    st.subheader("Data Entry")
    st.caption(f"Site: {site_label} | Logged by: {user_email}")

    entry_type = st.selectbox(
        "What do you want to log?",
        ["Birth", "Maternal Event", "Ward Census", "Incident", "Audit Score", "Training Record"],
    )

    if entry_type == "Birth":
        forms.birth_form(selected_site, user_email)
    elif entry_type == "Maternal Event":
        forms.maternal_event_form(selected_site, user_email)
    elif entry_type == "Ward Census":
        forms.ward_census_form(selected_site, user_email)
    elif entry_type == "Incident":
        forms.incident_form(selected_site, user_email)
    elif entry_type == "Audit Score":
        forms.audit_form(selected_site, user_email)
    elif entry_type == "Training Record":
        forms.training_form(selected_site, user_email)
