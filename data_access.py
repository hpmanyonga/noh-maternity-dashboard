# Supabase data access layer for NOH Maternity Dashboard

import os
import streamlit as st
from datetime import date, timedelta


def _get_supabase():
    """Return a Supabase client, trying st.secrets first then env vars."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception:
            pass
    return None


def get_sb():
    """Public accessor — returns client or None."""
    return _get_supabase()


# --- Births ---

@st.cache_data(ttl=120)
def get_births(site, date_from, date_to):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        result = (
            sb.table("births")
            .select("*")
            .eq("site", site)
            .gte("birth_date", date_from.isoformat())
            .lte("birth_date", date_to.isoformat())
            .order("birth_date", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def insert_birth(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("births").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- Maternal Events ---

@st.cache_data(ttl=120)
def get_maternal_events(site, date_from, date_to):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        result = (
            sb.table("maternal_events")
            .select("*")
            .eq("site", site)
            .gte("event_date", date_from.isoformat())
            .lte("event_date", date_to.isoformat())
            .order("event_date", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def insert_maternal_event(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("maternal_events").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- Ward Census ---

@st.cache_data(ttl=120)
def get_ward_census(site, census_date):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        result = (
            sb.table("ward_census")
            .select("*")
            .eq("site", site)
            .eq("census_date", census_date.isoformat())
            .execute()
        )
        return result.data or []
    except Exception:
        return []


@st.cache_data(ttl=120)
def get_ward_census_range(site, date_from, date_to):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        result = (
            sb.table("ward_census")
            .select("*")
            .eq("site", site)
            .gte("census_date", date_from.isoformat())
            .lte("census_date", date_to.isoformat())
            .order("census_date", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def upsert_ward_census(records):
    """Upsert a list of ward census records (one per ward)."""
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("ward_census").upsert(
        records, on_conflict="site,census_date,ward"
    ).execute()
    st.cache_data.clear()
    return result.data


# --- Antenatal Bookings ---

@st.cache_data(ttl=300)
def get_antenatal_bookings(site, active_only=True):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        q = sb.table("antenatal_bookings").select("*").eq("site", site)
        if active_only:
            q = q.eq("is_active", True)
        result = q.order("edd").execute()
        return result.data or []
    except Exception:
        return []


def insert_antenatal_booking(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("antenatal_bookings").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- Incidents ---

@st.cache_data(ttl=120)
def get_incidents(site, date_from=None, date_to=None, status=None):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        q = sb.table("incidents").select("*").eq("site", site)
        if date_from:
            q = q.gte("incident_date", date_from.isoformat())
        if date_to:
            q = q.lte("incident_date", date_to.isoformat())
        if status:
            q = q.eq("status", status)
        result = q.order("incident_date", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def insert_incident(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("incidents").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- Audit Scores ---

@st.cache_data(ttl=300)
def get_audit_scores(site, date_from=None, date_to=None):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        q = sb.table("audit_scores").select("*").eq("site", site)
        if date_from:
            q = q.gte("audit_date", date_from.isoformat())
        if date_to:
            q = q.lte("audit_date", date_to.isoformat())
        result = q.order("audit_date", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def insert_audit_score(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("audit_scores").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- Staff Training ---

@st.cache_data(ttl=300)
def get_staff_training(site, date_from=None, date_to=None):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        q = sb.table("staff_training").select("*").eq("site", site)
        if date_from:
            q = q.gte("training_date", date_from.isoformat())
        if date_to:
            q = q.lte("training_date", date_to.isoformat())
        result = q.order("training_date", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def insert_staff_training(data):
    sb = _get_supabase()
    if not sb:
        raise RuntimeError("Supabase not available")
    result = sb.table("staff_training").insert(data).execute()
    st.cache_data.clear()
    return result.data


# --- KPI Targets ---

@st.cache_data(ttl=600)
def get_kpi_targets(site):
    sb = _get_supabase()
    if not sb:
        return []
    try:
        result = sb.table("kpi_targets").select("*").eq("site", site).execute()
        return result.data or []
    except Exception:
        return []
