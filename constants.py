# NOH Maternity Team Dashboard — Constants

SITES = {
    "pta": {"label": "Pretoria"},
    "jhb": {"label": "Johannesburg"},
    "rus": {"label": "Rustenburg"},
}

# NOH colour palette
NOH_TEAL       = "#599591"
NOH_TEAL_DARK  = "#2e6b68"
NOH_PINK_LIGHT = "#f3bdc4"
NOH_PINK_DARK  = "#d4878f"
NOH_GOLD       = "#e8c07a"
NOH_PURPLE     = "#7b5ea7"
NOH_BLUE       = "#3a8582"
NOH_SAGE       = "#a8d5d3"

# RAG colours
RAG_GREEN  = "#2e7d32"
RAG_AMBER  = "#f57f17"
RAG_RED    = "#c62828"
RAG_GREY   = "#9e9e9e"

RAG_BG = {
    "green":  "#e8f5e9",
    "amber":  "#fff8e1",
    "red":    "#ffebee",
    "grey":   "#f5f5f5",
}

# Delivery modes
DELIVERY_MODES = [
    "nvd",
    "assisted_vacuum",
    "assisted_forceps",
    "elective_cs",
    "emergency_cs",
]

DELIVERY_MODE_LABELS = {
    "nvd":              "NVD",
    "assisted_vacuum":  "Assisted (Vacuum)",
    "assisted_forceps": "Assisted (Forceps)",
    "elective_cs":      "Elective CS",
    "emergency_cs":     "Emergency CS",
}

# Baby outcomes
BABY_OUTCOMES = [
    "live_well",
    "live_nicu",
    "stillbirth_macerated",
    "stillbirth_fresh",
    "early_nnd",
    "late_nnd",
]

BABY_OUTCOME_LABELS = {
    "live_well":              "Live — Well",
    "live_nicu":              "Live — NICU admission",
    "stillbirth_macerated":   "Stillbirth (Macerated)",
    "stillbirth_fresh":       "Stillbirth (Fresh)",
    "early_nnd":              "Early neonatal death (0-7d)",
    "late_nnd":               "Late neonatal death (8-28d)",
}

# Maternal event types
MATERNAL_EVENT_TYPES = [
    "pph_severe",
    "eclampsia",
    "severe_preeclampsia",
    "icu_admission",
    "maternal_near_miss",
    "maternal_death",
    "uterine_rupture",
    "unplanned_hysterectomy",
    "blood_transfusion",
    "anaesthetic_complication",
    "other",
]

MATERNAL_EVENT_LABELS = {
    "pph_severe":               "Severe PPH (>1500ml)",
    "eclampsia":                "Eclampsia",
    "severe_preeclampsia":      "Severe pre-eclampsia",
    "icu_admission":            "ICU admission",
    "maternal_near_miss":       "Maternal near-miss",
    "maternal_death":           "Maternal death",
    "uterine_rupture":          "Uterine rupture",
    "unplanned_hysterectomy":   "Unplanned hysterectomy",
    "blood_transfusion":        "Blood transfusion",
    "anaesthetic_complication": "Anaesthetic complication",
    "other":                    "Other",
}

# Wards
WARDS = ["antenatal", "labour", "postnatal", "nursery_well", "nicu"]

WARD_LABELS = {
    "antenatal":    "Antenatal Ward",
    "labour":       "Labour Ward",
    "postnatal":    "Postnatal Ward",
    "nursery_well": "Well Baby Nursery",
    "nicu":         "NICU",
}

# Incident categories
INCIDENT_CATEGORIES = [
    "clinical", "medication", "fall", "ipc",
    "equipment", "communication", "other",
]

# SAC ratings
SAC_RATINGS = {
    1: "SAC 1 — Catastrophic",
    2: "SAC 2 — Major",
    3: "SAC 3 — Moderate",
    4: "SAC 4 — Minor",
}

# Audit types
AUDIT_TYPES = [
    "partograph", "medication_chart", "ipc", "hand_hygiene",
    "patient_record", "consent", "theatre_checklist",
]

AUDIT_TYPE_LABELS = {
    "partograph":       "Partograph Audit",
    "medication_chart": "Medication Chart Audit",
    "ipc":              "IPC Audit",
    "hand_hygiene":     "Hand Hygiene Audit",
    "patient_record":   "Patient Record Audit",
    "consent":          "Consent Audit",
    "theatre_checklist": "Theatre Checklist Audit",
}

# Staff roles
STAFF_ROLES = ["midwife", "medical_officer", "obstetrician", "anaesthetist", "nurse"]

# Training types
TRAINING_TYPES = [
    "competency_assessment", "emergency_drill", "mandatory_training", "esmoe",
]

# Risk categories
RISK_CATEGORIES = ["low", "intermediate", "high"]

# SOP references (from NOH Clinical Manual)
SOP_REFERENCES = {
    "SOP-001": "Controlled Drugs Management",
    "SOP-002": "Major Haemorrhage Protocol",
    "SOP-003": "Normal Labour and Delivery",
    "SOP-004": "Hypertensive Disorders",
    "SOP-005": "Shoulder Dystocia",
    "SOP-006": "Cord Prolapse",
    "SOP-007": "Caesarean Section Pathway",
    "SOP-008": "Neonatal Resuscitation",
    "SOP-009": "HIV in Pregnancy (PMTCT)",
    "SOP-010": "Referral and Transfer",
    "SOP-011": "Blood Transfusion and MTP",
}
