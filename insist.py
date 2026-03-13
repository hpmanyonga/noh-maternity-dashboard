# INSIST perinatal death classification — South African standard
# Based on ICD-PM / PPIP classification system

INSIST_PRIMARY_CAUSES = {
    "spontaneous_preterm":      "Spontaneous preterm labour",
    "hypertensive":             "Hypertensive disorders",
    "antepartum_haemorrhage":   "Antepartum haemorrhage",
    "intrapartum_asphyxia":     "Intrapartum asphyxia/birth trauma",
    "fetal_abnormality":        "Fetal abnormality",
    "infection":                "Infections",
    "iugr":                     "Intrauterine growth restriction",
    "unexplained_iud":          "Unexplained intrauterine death",
    "maternal_disease":         "Maternal disease",
    "trauma":                   "Trauma",
    "other":                    "Other / Unclassified",
}

INSIST_FINAL_CAUSES = {
    "hypoxia":          "Hypoxia / Asphyxia",
    "immaturity":       "Immaturity-related",
    "infection":        "Infection",
    "congenital":       "Congenital abnormality",
    "trauma":           "Birth trauma",
    "unexplained":      "Unexplained",
    "other":            "Other",
}

AVOIDABLE_FACTORS = {
    "none":             "No avoidable factor identified",
    "patient":          "Patient-related factor",
    "admin":            "Administrative/system factor",
    "health_worker":    "Health worker-related factor",
    "multiple":         "Multiple factors",
}

DEATH_OUTCOMES = {"stillbirth_macerated", "stillbirth_fresh", "early_nnd", "late_nnd"}


def is_perinatal_death(baby_outcome):
    return baby_outcome in DEATH_OUTCOMES


def is_stillbirth(baby_outcome):
    return baby_outcome in {"stillbirth_macerated", "stillbirth_fresh"}


def is_neonatal_death(baby_outcome):
    return baby_outcome in {"early_nnd", "late_nnd"}
