# Data entry forms for the NOH Maternity Team Dashboard

import streamlit as st
from datetime import date, time, datetime
from constants import (
    DELIVERY_MODES, DELIVERY_MODE_LABELS, BABY_OUTCOMES, BABY_OUTCOME_LABELS,
    MATERNAL_EVENT_TYPES, MATERNAL_EVENT_LABELS,
    WARDS, WARD_LABELS, INCIDENT_CATEGORIES, SAC_RATINGS,
    AUDIT_TYPES, AUDIT_TYPE_LABELS, STAFF_ROLES, TRAINING_TYPES,
    SOP_REFERENCES, RISK_CATEGORIES,
)
from insist import (
    INSIST_PRIMARY_CAUSES, INSIST_FINAL_CAUSES, AVOIDABLE_FACTORS,
    is_perinatal_death,
)
from data_access import (
    insert_birth, insert_maternal_event, upsert_ward_census,
    insert_incident, insert_audit_score, insert_staff_training,
    insert_antenatal_booking,
)


def birth_form(site, user_email):
    """Render the birth registration form. Returns True if submitted."""
    with st.form("birth_form", clear_on_submit=True):
        st.subheader("Log New Birth")

        col1, col2, col3 = st.columns(3)
        with col1:
            birth_date = st.date_input("Birth date", value=date.today())
            birth_time = st.time_input("Birth time", value=time(8, 0))
            patient_id = st.text_input("Patient ID (hospital number)")
        with col2:
            delivery_mode = st.selectbox(
                "Delivery mode",
                options=DELIVERY_MODES,
                format_func=lambda m: DELIVERY_MODE_LABELS[m],
            )
            gestational_age = st.number_input("Gestational age (weeks)", 20, 44, 39)
            gravidity = st.number_input("Gravidity", 1, 15, 1)
            parity = st.number_input("Parity", 0, 15, 0)
        with col3:
            baby_outcome = st.selectbox(
                "Baby outcome",
                options=BABY_OUTCOMES,
                format_func=lambda o: BABY_OUTCOME_LABELS[o],
            )
            birth_weight = st.number_input("Birth weight (g)", 300, 6000, 3200, step=50)
            baby_gender = st.selectbox("Baby gender", ["male", "female", "indeterminate"])

        st.divider()

        col4, col5, col6 = st.columns(3)
        with col4:
            apgar_1 = st.number_input("Apgar 1 min", 0, 10, 8)
            apgar_5 = st.number_input("Apgar 5 min", 0, 10, 9)
            apgar_10 = st.number_input("Apgar 10 min", 0, 10, 9)
        with col5:
            ebl = st.number_input("Estimated blood loss (ml)", 0, 5000, 300, step=50)
            is_induction = st.checkbox("Induction of labour")
            is_vbac = st.checkbox("VBAC attempt")
            vbac_success = st.checkbox("VBAC successful") if is_vbac else False
        with col6:
            episiotomy = st.checkbox("Episiotomy performed")
            tear_degree = st.selectbox("Perineal tear degree", [0, 1, 2, 3, 4])
            labour_hrs = st.number_input("Labour duration (hrs)", 0.0, 72.0, 8.0, step=0.5)

        st.divider()

        col7, col8 = st.columns(2)
        with col7:
            st.markdown("**Newborn care**")
            skin_to_skin = st.checkbox("Skin-to-skin within 1hr", value=True)
            bf_initiated = st.checkbox("Breastfeeding initiated within 1hr", value=True)
            nicu = st.checkbox("NICU admission")
            partograph = st.checkbox("Partograph completed", value=True)
            active_3rd = st.checkbox("Active management 3rd stage", value=True)

        with col8:
            st.markdown("**PMTCT**")
            hiv_tested = st.checkbox("HIV tested", value=True)
            hiv_positive = st.checkbox("HIV positive")
            on_art = st.checkbox("On ART") if hiv_positive else False
            pcr_done = st.checkbox("Infant PCR done") if hiv_positive else False

        # INSIST fields (conditional on death)
        insist_primary = None
        insist_final = None
        insist_avoidable = None
        if is_perinatal_death(baby_outcome):
            st.divider()
            st.markdown("**INSIST Classification** (perinatal death)")
            insist_primary = st.selectbox(
                "Primary obstetric cause",
                options=list(INSIST_PRIMARY_CAUSES.keys()),
                format_func=lambda c: INSIST_PRIMARY_CAUSES[c],
            )
            insist_final = st.selectbox(
                "Final cause of death",
                options=list(INSIST_FINAL_CAUSES.keys()),
                format_func=lambda c: INSIST_FINAL_CAUSES[c],
            )
            insist_avoidable = st.selectbox(
                "Avoidable factor",
                options=list(AVOIDABLE_FACTORS.keys()),
                format_func=lambda c: AVOIDABLE_FACTORS[c],
            )

        notes = st.text_area("Notes", height=80)

        submitted = st.form_submit_button("Save Birth Record", type="primary")

        if submitted:
            pph_flag = (
                (ebl > 500 and delivery_mode == "nvd") or
                (ebl > 1000 and delivery_mode in ["elective_cs", "emergency_cs"]) or
                (ebl > 500)
            )
            data = {
                "site": site,
                "birth_date": birth_date.isoformat(),
                "birth_time": birth_time.isoformat(),
                "patient_id": patient_id or None,
                "gestational_age_weeks": gestational_age,
                "gravidity": gravidity,
                "parity": parity,
                "delivery_mode": delivery_mode,
                "is_vbac_attempt": is_vbac,
                "vbac_successful": vbac_success if is_vbac else None,
                "is_induction": is_induction,
                "labour_duration_hrs": labour_hrs,
                "episiotomy": episiotomy,
                "perineal_tear_degree": tear_degree,
                "ebl_ml": ebl,
                "pph": pph_flag,
                "active_third_stage": active_3rd,
                "skin_to_skin_1hr": skin_to_skin,
                "breastfeeding_initiated_1hr": bf_initiated,
                "partograph_completed": partograph,
                "apgar_1min": apgar_1,
                "apgar_5min": apgar_5,
                "apgar_10min": apgar_10,
                "birth_weight_g": birth_weight,
                "baby_gender": baby_gender,
                "baby_outcome": baby_outcome,
                "nicu_admission": nicu,
                "pmtct_hiv_tested": hiv_tested,
                "pmtct_hiv_positive": hiv_positive,
                "pmtct_on_art": on_art if hiv_positive else None,
                "pmtct_infant_pcr_done": pcr_done if hiv_positive else None,
                "insist_primary_cause": insist_primary,
                "insist_final_cause": insist_final,
                "insist_avoidable_factor": insist_avoidable,
                "notes": notes or None,
                "created_by": user_email,
            }
            try:
                insert_birth(data)
                st.success("Birth record saved.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False


def maternal_event_form(site, user_email):
    """Maternal adverse event form."""
    with st.form("maternal_event_form", clear_on_submit=True):
        st.subheader("Log Maternal Event")

        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event date", value=date.today())
            event_type = st.selectbox(
                "Event type",
                options=MATERNAL_EVENT_TYPES,
                format_func=lambda t: MATERNAL_EVENT_LABELS[t],
            )
            severity = st.selectbox("Severity", ["moderate", "severe", "life_threatening", "death"])
        with col2:
            ebl = st.number_input("EBL (ml, if PPH)", 0, 10000, 0, step=100)
            blood_units = st.number_input("Blood units transfused", 0, 20, 0)
            icu_days = st.number_input("ICU days", 0, 30, 0)

        description = st.text_area("Description", height=100)
        submitted = st.form_submit_button("Save Event", type="primary")

        if submitted:
            data = {
                "site": site,
                "event_date": event_date.isoformat(),
                "event_type": event_type,
                "severity": severity,
                "ebl_ml": ebl if ebl > 0 else None,
                "blood_units_transfused": blood_units if blood_units > 0 else None,
                "icu_days": icu_days if icu_days > 0 else None,
                "description": description,
                "created_by": user_email,
            }
            try:
                insert_maternal_event(data)
                st.success("Maternal event saved.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False


def ward_census_form(site, user_email):
    """Ward census form — quick grid entry."""
    with st.form("ward_census_form"):
        st.subheader("Ward Census")
        census_date = st.date_input("Census date", value=date.today())

        # Default bed capacities per ward
        defaults = {
            "antenatal": 8, "labour": 6, "postnatal": 12,
            "nursery_well": 10, "nicu": 4,
        }

        records = []
        for ward in WARDS:
            st.markdown(f"**{WARD_LABELS[ward]}**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                patients = st.number_input(f"Patients", 0, 50, 0, key=f"census_{ward}_pts")
            with c2:
                capacity = st.number_input(f"Bed capacity", 1, 50, defaults.get(ward, 10), key=f"census_{ward}_cap")
            with c3:
                admissions = st.number_input(f"Admissions", 0, 20, 0, key=f"census_{ward}_adm")
            with c4:
                midwives = st.number_input(f"Midwives on duty", 0, 10, 0, key=f"census_{ward}_mw")

            records.append({
                "site": site,
                "census_date": census_date.isoformat(),
                "ward": ward,
                "patients_count": patients,
                "bed_capacity": capacity,
                "admissions": admissions,
                "discharges": 0,
                "midwives_on_duty": midwives,
                "created_by": user_email,
            })

        submitted = st.form_submit_button("Save Census", type="primary")
        if submitted:
            try:
                upsert_ward_census(records)
                st.success("Ward census saved.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False


def incident_form(site, user_email):
    """Clinical incident report form."""
    with st.form("incident_form", clear_on_submit=True):
        st.subheader("Log Incident")

        col1, col2 = st.columns(2)
        with col1:
            incident_date = st.date_input("Incident date", value=date.today())
            reported_date = st.date_input("Reported date", value=date.today())
            sac = st.selectbox("SAC rating", options=[1, 2, 3, 4], format_func=lambda s: SAC_RATINGS[s])
        with col2:
            category = st.selectbox("Category", options=INCIDENT_CATEGORIES, format_func=lambda c: c.replace("_", " ").title())
            patient_harm = st.selectbox("Patient harm", ["none", "minor", "moderate", "severe", "death"])

        description = st.text_area("Description", height=100)
        submitted = st.form_submit_button("Save Incident", type="primary")

        if submitted:
            due_days = 3 if sac <= 2 else 14
            data = {
                "site": site,
                "incident_date": incident_date.isoformat(),
                "reported_date": reported_date.isoformat(),
                "sac_rating": sac,
                "category": category,
                "description": description,
                "patient_harm": patient_harm,
                "status": "open",
                "investigation_due_date": (incident_date + __import__('datetime').timedelta(days=due_days)).isoformat(),
                "created_by": user_email,
            }
            try:
                insert_incident(data)
                st.success("Incident logged.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False


def audit_form(site, user_email):
    """Clinical audit score form."""
    with st.form("audit_form", clear_on_submit=True):
        st.subheader("Log Audit Score")

        col1, col2 = st.columns(2)
        with col1:
            audit_date = st.date_input("Audit date", value=date.today())
            audit_type = st.selectbox(
                "Audit type", options=AUDIT_TYPES,
                format_func=lambda t: AUDIT_TYPE_LABELS[t],
            )
        with col2:
            score = st.number_input("Score (%)", 0, 100, 80)
            sample_size = st.number_input("Sample size", 1, 200, 10)
            auditor = st.text_input("Auditor name")

        findings = st.text_area("Key findings", height=80)
        submitted = st.form_submit_button("Save Audit", type="primary")

        if submitted:
            data = {
                "site": site,
                "audit_date": audit_date.isoformat(),
                "audit_type": audit_type,
                "score_pct": score,
                "sample_size": sample_size,
                "auditor": auditor or None,
                "findings": findings or None,
                "created_by": user_email,
            }
            try:
                insert_audit_score(data)
                st.success("Audit score saved.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False


def training_form(site, user_email):
    """Staff training / competency form."""
    with st.form("training_form", clear_on_submit=True):
        st.subheader("Log Training / Competency")

        col1, col2 = st.columns(2)
        with col1:
            staff_name = st.text_input("Staff name")
            staff_role = st.selectbox("Role", options=STAFF_ROLES, format_func=lambda r: r.replace("_", " ").title())
            training_type = st.selectbox("Training type", options=TRAINING_TYPES, format_func=lambda t: t.replace("_", " ").title())
        with col2:
            training_date = st.date_input("Training date", value=date.today())
            sop_ref = st.selectbox(
                "SOP reference (optional)",
                options=[""] + list(SOP_REFERENCES.keys()),
                format_func=lambda s: f"{s} - {SOP_REFERENCES[s]}" if s else "N/A",
            )
            score = st.number_input("Score (%)", 0, 100, 80)
            passed = st.checkbox("Passed", value=True)

        submitted = st.form_submit_button("Save Training Record", type="primary")

        if submitted:
            if not staff_name:
                st.error("Staff name is required.")
                return False
            data = {
                "site": site,
                "staff_name": staff_name,
                "staff_role": staff_role,
                "training_type": training_type,
                "sop_reference": sop_ref or None,
                "training_date": training_date.isoformat(),
                "score_pct": score,
                "passed": passed,
                "created_by": user_email,
            }
            try:
                insert_staff_training(data)
                st.success("Training record saved.")
                return True
            except Exception as e:
                st.error(f"Failed to save: {e}")
    return False
