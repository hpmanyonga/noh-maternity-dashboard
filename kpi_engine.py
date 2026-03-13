# KPI computation and RAG threshold engine

import pandas as pd
from constants import RAG_GREEN, RAG_AMBER, RAG_RED, RAG_GREY


def rag_status(value, green_max, amber_max, direction):
    """Compute RAG status for a KPI value."""
    if value is None:
        return "grey"
    if direction == "lower_is_better":
        if value <= green_max:
            return "green"
        if value <= amber_max:
            return "amber"
        return "red"
    else:  # higher_is_better
        if value >= green_max:
            return "green"
        if value >= amber_max:
            return "amber"
        return "red"


def rag_color(status):
    return {
        "green": RAG_GREEN,
        "amber": RAG_AMBER,
        "red":   RAG_RED,
        "grey":  RAG_GREY,
    }.get(status, RAG_GREY)


# Default KPI targets (used if kpi_targets table is empty)
DEFAULT_TARGETS = [
    {"kpi_code": "cs_rate",              "kpi_name": "CS Rate (Overall)",           "green_max": 30,  "amber_max": 40,  "unit": "%",        "direction": "lower_is_better",  "source": "WHO/SASOG"},
    {"kpi_code": "emergency_cs_rate",    "kpi_name": "Emergency CS Rate",           "green_max": 12,  "amber_max": 18,  "unit": "%",        "direction": "lower_is_better",  "source": "NOH Internal"},
    {"kpi_code": "pnmr",                "kpi_name": "Perinatal Mortality Rate",    "green_max": 15,  "amber_max": 25,  "unit": "per_1000", "direction": "lower_is_better",  "source": "NDoH"},
    {"kpi_code": "sbr",                 "kpi_name": "Stillbirth Rate",             "green_max": 10,  "amber_max": 18,  "unit": "per_1000", "direction": "lower_is_better",  "source": "WHO/NDoH"},
    {"kpi_code": "fresh_sbr",           "kpi_name": "Fresh Stillbirth Rate",       "green_max": 5,   "amber_max": 10,  "unit": "per_1000", "direction": "lower_is_better",  "source": "PPIP/NDoH"},
    {"kpi_code": "enndr",               "kpi_name": "Early Neonatal Death Rate",   "green_max": 5,   "amber_max": 10,  "unit": "per_1000", "direction": "lower_is_better",  "source": "NDoH"},
    {"kpi_code": "pph_rate",            "kpi_name": "PPH Rate",                    "green_max": 5,   "amber_max": 10,  "unit": "%",        "direction": "lower_is_better",  "source": "RCOG/WHO"},
    {"kpi_code": "severe_pph_rate",     "kpi_name": "Severe PPH Rate (>1500ml)",   "green_max": 1,   "amber_max": 3,   "unit": "%",        "direction": "lower_is_better",  "source": "RCOG"},
    {"kpi_code": "episiotomy_rate",     "kpi_name": "Episiotomy Rate",             "green_max": 15,  "amber_max": 25,  "unit": "%",        "direction": "lower_is_better",  "source": "WHO"},
    {"kpi_code": "tear_3_4_rate",       "kpi_name": "3rd/4th Degree Tear Rate",   "green_max": 1.5, "amber_max": 3,   "unit": "%",        "direction": "lower_is_better",  "source": "RCOG"},
    {"kpi_code": "skin_to_skin_rate",   "kpi_name": "Skin-to-Skin within 1hr",    "green_max": 80,  "amber_max": 60,  "unit": "%",        "direction": "higher_is_better", "source": "WHO/NDoH"},
    {"kpi_code": "bf_initiation_rate",  "kpi_name": "BF Initiation within 1hr",   "green_max": 75,  "amber_max": 50,  "unit": "%",        "direction": "higher_is_better", "source": "WHO BFHI"},
    {"kpi_code": "apgar_low_rate",      "kpi_name": "Apgar <7 at 5min Rate",      "green_max": 3,   "amber_max": 6,   "unit": "%",        "direction": "lower_is_better",  "source": "NOH Internal"},
    {"kpi_code": "pmtct_testing_rate",  "kpi_name": "PMTCT HIV Testing Rate",     "green_max": 95,  "amber_max": 85,  "unit": "%",        "direction": "higher_is_better", "source": "NDoH 95-95-95"},
    {"kpi_code": "partograph_rate",     "kpi_name": "Partograph Completion Rate",  "green_max": 90,  "amber_max": 75,  "unit": "%",        "direction": "higher_is_better", "source": "NDoH/SOP-003"},
    {"kpi_code": "bed_occupancy",       "kpi_name": "Labour Ward Occupancy",       "green_max": 80,  "amber_max": 95,  "unit": "%",        "direction": "lower_is_better",  "source": "Healthcare standard"},
    {"kpi_code": "competency_rate",     "kpi_name": "Staff Competency Compliance", "green_max": 90,  "amber_max": 75,  "unit": "%",        "direction": "higher_is_better", "source": "NOH Ch.11"},
    {"kpi_code": "drill_rate",          "kpi_name": "Emergency Drill Completion",  "green_max": 95,  "amber_max": 80,  "unit": "%",        "direction": "higher_is_better", "source": "NOH Ch.12"},
    {"kpi_code": "audit_score",         "kpi_name": "Clinical Audit Score",        "green_max": 80,  "amber_max": 60,  "unit": "%",        "direction": "higher_is_better", "source": "NOH governance"},
    {"kpi_code": "avg_los_nvd",         "kpi_name": "Average LOS - NVD",           "green_max": 1.5, "amber_max": 2.5, "unit": "days",     "direction": "lower_is_better",  "source": "SA private"},
    {"kpi_code": "avg_los_cs",          "kpi_name": "Average LOS - CS",            "green_max": 3,   "amber_max": 4,   "unit": "days",     "direction": "lower_is_better",  "source": "SA private"},
]


def get_targets_map(targets_df=None):
    """Return dict of kpi_code -> target dict. Uses defaults if no DB data."""
    if targets_df is not None and not targets_df.empty:
        return {r["kpi_code"]: r for _, r in targets_df.iterrows()}
    return {t["kpi_code"]: t for t in DEFAULT_TARGETS}


def safe_pct(numerator, denominator):
    if denominator == 0:
        return None
    return round(numerator / denominator * 100, 1)


def safe_rate_per_1000(numerator, denominator):
    if denominator == 0:
        return None
    return round(numerator / denominator * 1000, 1)


def compute_birth_kpis(births_df, targets_map):
    """Compute KPIs from a births DataFrame. Returns list of KPI dicts."""
    n = len(births_df)
    if n == 0:
        return []

    kpis = []

    # CS rate
    cs_count = len(births_df[births_df["delivery_mode"].isin(["elective_cs", "emergency_cs"])])
    cs_val = safe_pct(cs_count, n)
    t = targets_map.get("cs_rate", {})
    kpis.append({
        "code": "cs_rate", "name": t.get("kpi_name", "CS Rate"),
        "value": cs_val, "unit": "%",
        "rag": rag_status(cs_val, t.get("green_max", 30), t.get("amber_max", 40), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Emergency CS rate
    emg_cs = len(births_df[births_df["delivery_mode"] == "emergency_cs"])
    emg_val = safe_pct(emg_cs, n)
    t = targets_map.get("emergency_cs_rate", {})
    kpis.append({
        "code": "emergency_cs_rate", "name": t.get("kpi_name", "Emergency CS Rate"),
        "value": emg_val, "unit": "%",
        "rag": rag_status(emg_val, t.get("green_max", 12), t.get("amber_max", 18), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Perinatal mortality rate
    total_births = n
    deaths = len(births_df[births_df["baby_outcome"].isin(
        ["stillbirth_macerated", "stillbirth_fresh", "early_nnd", "late_nnd"]
    )])
    pnmr_val = safe_rate_per_1000(deaths, total_births)
    t = targets_map.get("pnmr", {})
    kpis.append({
        "code": "pnmr", "name": t.get("kpi_name", "Perinatal Mortality Rate"),
        "value": pnmr_val, "unit": "per 1000",
        "rag": rag_status(pnmr_val, t.get("green_max", 15), t.get("amber_max", 25), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Stillbirth rate
    sb = len(births_df[births_df["baby_outcome"].isin(["stillbirth_macerated", "stillbirth_fresh"])])
    sbr_val = safe_rate_per_1000(sb, total_births)
    t = targets_map.get("sbr", {})
    kpis.append({
        "code": "sbr", "name": t.get("kpi_name", "Stillbirth Rate"),
        "value": sbr_val, "unit": "per 1000",
        "rag": rag_status(sbr_val, t.get("green_max", 10), t.get("amber_max", 18), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Fresh stillbirth rate
    fsb = len(births_df[births_df["baby_outcome"] == "stillbirth_fresh"])
    fsb_val = safe_rate_per_1000(fsb, total_births)
    t = targets_map.get("fresh_sbr", {})
    kpis.append({
        "code": "fresh_sbr", "name": t.get("kpi_name", "Fresh Stillbirth Rate"),
        "value": fsb_val, "unit": "per 1000",
        "rag": rag_status(fsb_val, t.get("green_max", 5), t.get("amber_max", 10), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # ENND rate (per 1000 live births)
    live_births = len(births_df[births_df["baby_outcome"].isin(["live_well", "live_nicu"])])
    ennd = len(births_df[births_df["baby_outcome"] == "early_nnd"])
    ennd_val = safe_rate_per_1000(ennd, live_births)
    t = targets_map.get("enndr", {})
    kpis.append({
        "code": "enndr", "name": t.get("kpi_name", "Early Neonatal Death Rate"),
        "value": ennd_val, "unit": "per 1000",
        "rag": rag_status(ennd_val, t.get("green_max", 5), t.get("amber_max", 10), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # PPH rate
    pph = len(births_df[births_df["pph"] == True])
    pph_val = safe_pct(pph, n)
    t = targets_map.get("pph_rate", {})
    kpis.append({
        "code": "pph_rate", "name": t.get("kpi_name", "PPH Rate"),
        "value": pph_val, "unit": "%",
        "rag": rag_status(pph_val, t.get("green_max", 5), t.get("amber_max", 10), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Severe PPH rate
    severe_pph = len(births_df[births_df["ebl_ml"] > 1500]) if "ebl_ml" in births_df.columns else 0
    spph_val = safe_pct(severe_pph, n)
    t = targets_map.get("severe_pph_rate", {})
    kpis.append({
        "code": "severe_pph_rate", "name": t.get("kpi_name", "Severe PPH Rate"),
        "value": spph_val, "unit": "%",
        "rag": rag_status(spph_val, t.get("green_max", 1), t.get("amber_max", 3), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Episiotomy rate
    epis = len(births_df[births_df["episiotomy"] == True])
    epis_val = safe_pct(epis, n)
    t = targets_map.get("episiotomy_rate", {})
    kpis.append({
        "code": "episiotomy_rate", "name": t.get("kpi_name", "Episiotomy Rate"),
        "value": epis_val, "unit": "%",
        "rag": rag_status(epis_val, t.get("green_max", 15), t.get("amber_max", 25), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # 3rd/4th degree tears
    tears = len(births_df[births_df["perineal_tear_degree"].isin([3, 4])]) if "perineal_tear_degree" in births_df.columns else 0
    tear_val = safe_pct(tears, n)
    t = targets_map.get("tear_3_4_rate", {})
    kpis.append({
        "code": "tear_3_4_rate", "name": t.get("kpi_name", "3rd/4th Degree Tear Rate"),
        "value": tear_val, "unit": "%",
        "rag": rag_status(tear_val, t.get("green_max", 1.5), t.get("amber_max", 3), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # Skin-to-skin
    sts_eligible = births_df[births_df["baby_outcome"].isin(["live_well", "live_nicu"])]
    sts = len(sts_eligible[sts_eligible["skin_to_skin_1hr"] == True]) if not sts_eligible.empty else 0
    sts_val = safe_pct(sts, len(sts_eligible))
    t = targets_map.get("skin_to_skin_rate", {})
    kpis.append({
        "code": "skin_to_skin_rate", "name": t.get("kpi_name", "Skin-to-Skin within 1hr"),
        "value": sts_val, "unit": "%",
        "rag": rag_status(sts_val, t.get("green_max", 80), t.get("amber_max", 60), "higher_is_better"),
        "source": t.get("source", ""),
    })

    # BF initiation
    bf = len(sts_eligible[sts_eligible["breastfeeding_initiated_1hr"] == True]) if not sts_eligible.empty else 0
    bf_val = safe_pct(bf, len(sts_eligible))
    t = targets_map.get("bf_initiation_rate", {})
    kpis.append({
        "code": "bf_initiation_rate", "name": t.get("kpi_name", "BF Initiation within 1hr"),
        "value": bf_val, "unit": "%",
        "rag": rag_status(bf_val, t.get("green_max", 75), t.get("amber_max", 50), "higher_is_better"),
        "source": t.get("source", ""),
    })

    # Apgar <7 at 5min
    apgar_eligible = births_df[births_df["apgar_5min"].notna()] if "apgar_5min" in births_df.columns else pd.DataFrame()
    low_apgar = len(apgar_eligible[apgar_eligible["apgar_5min"] < 7]) if not apgar_eligible.empty else 0
    apgar_val = safe_pct(low_apgar, len(apgar_eligible))
    t = targets_map.get("apgar_low_rate", {})
    kpis.append({
        "code": "apgar_low_rate", "name": t.get("kpi_name", "Apgar <7 at 5min Rate"),
        "value": apgar_val, "unit": "%",
        "rag": rag_status(apgar_val, t.get("green_max", 3), t.get("amber_max", 6), "lower_is_better"),
        "source": t.get("source", ""),
    })

    # PMTCT testing rate
    pmtct_tested = len(births_df[births_df["pmtct_hiv_tested"] == True])
    pmtct_val = safe_pct(pmtct_tested, n)
    t = targets_map.get("pmtct_testing_rate", {})
    kpis.append({
        "code": "pmtct_testing_rate", "name": t.get("kpi_name", "PMTCT HIV Testing Rate"),
        "value": pmtct_val, "unit": "%",
        "rag": rag_status(pmtct_val, t.get("green_max", 95), t.get("amber_max", 85), "higher_is_better"),
        "source": t.get("source", ""),
    })

    # Partograph completion
    parto = len(births_df[births_df["partograph_completed"] == True])
    parto_val = safe_pct(parto, n)
    t = targets_map.get("partograph_rate", {})
    kpis.append({
        "code": "partograph_rate", "name": t.get("kpi_name", "Partograph Completion"),
        "value": parto_val, "unit": "%",
        "rag": rag_status(parto_val, t.get("green_max", 90), t.get("amber_max", 75), "higher_is_better"),
        "source": t.get("source", ""),
    })

    return kpis
