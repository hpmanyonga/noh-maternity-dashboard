"""Create Supabase tables for the NOH Maternity Team Dashboard.

Run this once to set up the schema:
    export SUPABASE_URL=https://zcjodsewjugovlmocgrz.supabase.co
    export SUPABASE_KEY=your-service-role-key
    python3 seed_tables.py

NOTE: This uses the Supabase SQL editor via the management API.
      You may need to run the SQL directly in the Supabase dashboard
      if the anon key doesn't have DDL permissions.
"""

SQL_SCHEMA = """
-- NOH Maternity Team Dashboard — Schema
-- Run in Supabase SQL Editor

-- 1. Births (central fact table)
CREATE TABLE IF NOT EXISTS births (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    birth_date DATE NOT NULL,
    birth_time TIME,
    patient_id TEXT,
    gestational_age_weeks INT,
    gravidity INT,
    parity INT,
    delivery_mode TEXT NOT NULL,
    is_vbac_attempt BOOLEAN DEFAULT false,
    vbac_successful BOOLEAN,
    is_induction BOOLEAN DEFAULT false,
    labour_duration_hrs NUMERIC,
    episiotomy BOOLEAN DEFAULT false,
    perineal_tear_degree INT DEFAULT 0,
    ebl_ml INT DEFAULT 0,
    pph BOOLEAN DEFAULT false,
    active_third_stage BOOLEAN DEFAULT true,
    skin_to_skin_1hr BOOLEAN,
    breastfeeding_initiated_1hr BOOLEAN,
    partograph_completed BOOLEAN,
    apgar_1min INT,
    apgar_5min INT,
    apgar_10min INT,
    birth_weight_g INT,
    baby_gender TEXT,
    baby_outcome TEXT NOT NULL,
    nicu_admission BOOLEAN DEFAULT false,
    pmtct_hiv_tested BOOLEAN,
    pmtct_hiv_positive BOOLEAN,
    pmtct_on_art BOOLEAN,
    pmtct_infant_pcr_done BOOLEAN,
    insist_primary_cause TEXT,
    insist_final_cause TEXT,
    insist_avoidable_factor TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_births_site_date ON births(site, birth_date);

-- 2. Maternal events
CREATE TABLE IF NOT EXISTS maternal_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    birth_id UUID REFERENCES births(id),
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT,
    ebl_ml INT,
    blood_units_transfused INT,
    icu_days INT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_maternal_events_site_date ON maternal_events(site, event_date);

-- 3. Ward census
CREATE TABLE IF NOT EXISTS ward_census (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    census_date DATE NOT NULL,
    ward TEXT NOT NULL,
    patients_count INT NOT NULL DEFAULT 0,
    bed_capacity INT NOT NULL DEFAULT 1,
    admissions INT DEFAULT 0,
    discharges INT DEFAULT 0,
    midwives_on_duty INT,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT,
    UNIQUE(site, census_date, ward)
);

-- 4. Antenatal bookings
CREATE TABLE IF NOT EXISTS antenatal_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    patient_id TEXT,
    booking_date DATE NOT NULL,
    edd DATE NOT NULL,
    risk_category TEXT DEFAULT 'low',
    hiv_status TEXT DEFAULT 'unknown',
    is_active BOOLEAN DEFAULT true,
    birth_id UUID REFERENCES births(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_antenatal_site_edd ON antenatal_bookings(site, edd);

-- 5. Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    incident_date DATE NOT NULL,
    reported_date DATE NOT NULL,
    sac_rating INT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    patient_harm TEXT DEFAULT 'none',
    status TEXT NOT NULL DEFAULT 'open',
    investigation_due_date DATE,
    root_cause TEXT,
    corrective_actions TEXT,
    closed_date DATE,
    linked_birth_id UUID REFERENCES births(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_incidents_site_date ON incidents(site, incident_date);

-- 6. Audit scores
CREATE TABLE IF NOT EXISTS audit_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    audit_date DATE NOT NULL,
    audit_type TEXT NOT NULL,
    score_pct NUMERIC NOT NULL,
    sample_size INT,
    auditor TEXT,
    findings TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

-- 7. Staff training
CREATE TABLE IF NOT EXISTS staff_training (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    staff_name TEXT NOT NULL,
    staff_role TEXT NOT NULL,
    training_type TEXT NOT NULL,
    sop_reference TEXT,
    training_date DATE NOT NULL,
    score_pct NUMERIC,
    passed BOOLEAN,
    expiry_date DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_training_site ON staff_training(site);

-- 8. KPI targets (configuration)
CREATE TABLE IF NOT EXISTS kpi_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    kpi_code TEXT NOT NULL,
    kpi_name TEXT NOT NULL,
    green_max NUMERIC,
    amber_max NUMERIC,
    unit TEXT,
    direction TEXT,
    source TEXT,
    UNIQUE(site, kpi_code)
);

-- 9. Daily summary (aggregation)
CREATE TABLE IF NOT EXISTS daily_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site TEXT NOT NULL,
    summary_date DATE NOT NULL,
    total_births INT DEFAULT 0,
    nvd_count INT DEFAULT 0,
    cs_count INT DEFAULT 0,
    elective_cs_count INT DEFAULT 0,
    emergency_cs_count INT DEFAULT 0,
    cs_rate_pct NUMERIC,
    pph_count INT DEFAULT 0,
    severe_pph_count INT DEFAULT 0,
    stillbirth_count INT DEFAULT 0,
    ennd_count INT DEFAULT 0,
    apgar_below7_at5_count INT DEFAULT 0,
    skin_to_skin_count INT DEFAULT 0,
    bf_initiated_count INT DEFAULT 0,
    episiotomy_count INT DEFAULT 0,
    tear_3_4_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(site, summary_date)
);

-- Enable RLS on all tables
ALTER TABLE births ENABLE ROW LEVEL SECURITY;
ALTER TABLE maternal_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ward_census ENABLE ROW LEVEL SECURITY;
ALTER TABLE antenatal_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_training ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_summary ENABLE ROW LEVEL SECURITY;

-- RLS policies: authenticated users can read and write all rows
-- (In production, refine per-site policies as needed)
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'births', 'maternal_events', 'ward_census', 'antenatal_bookings',
        'incidents', 'audit_scores', 'staff_training', 'kpi_targets', 'daily_summary'
    ]) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I_select ON %I', tbl, tbl);
        EXECUTE format('CREATE POLICY %I_select ON %I FOR SELECT TO authenticated USING (true)', tbl, tbl);
        EXECUTE format('DROP POLICY IF EXISTS %I_insert ON %I', tbl, tbl);
        EXECUTE format('CREATE POLICY %I_insert ON %I FOR INSERT TO authenticated WITH CHECK (true)', tbl, tbl);
        EXECUTE format('DROP POLICY IF EXISTS %I_update ON %I', tbl, tbl);
        EXECUTE format('CREATE POLICY %I_update ON %I FOR UPDATE TO authenticated USING (true)', tbl, tbl);
    END LOOP;
END $$;
"""


# Default KPI targets to seed
DEFAULT_KPI_TARGETS = [
    ("cs_rate",            "CS Rate (Overall)",           30,  40,  "%",        "lower_is_better",  "WHO/SASOG"),
    ("emergency_cs_rate",  "Emergency CS Rate",           12,  18,  "%",        "lower_is_better",  "NOH Internal"),
    ("pnmr",              "Perinatal Mortality Rate",    15,  25,  "per_1000", "lower_is_better",  "NDoH"),
    ("sbr",               "Stillbirth Rate",             10,  18,  "per_1000", "lower_is_better",  "WHO/NDoH"),
    ("fresh_sbr",         "Fresh Stillbirth Rate",       5,   10,  "per_1000", "lower_is_better",  "PPIP/NDoH"),
    ("enndr",             "Early Neonatal Death Rate",   5,   10,  "per_1000", "lower_is_better",  "NDoH"),
    ("pph_rate",          "PPH Rate",                    5,   10,  "%",        "lower_is_better",  "RCOG/WHO"),
    ("severe_pph_rate",   "Severe PPH Rate (>1500ml)",   1,   3,   "%",        "lower_is_better",  "RCOG"),
    ("episiotomy_rate",   "Episiotomy Rate",             15,  25,  "%",        "lower_is_better",  "WHO"),
    ("tear_3_4_rate",     "3rd/4th Degree Tear Rate",   1.5, 3,   "%",        "lower_is_better",  "RCOG"),
    ("skin_to_skin_rate", "Skin-to-Skin within 1hr",    80,  60,  "%",        "higher_is_better", "WHO/NDoH"),
    ("bf_initiation_rate","BF Initiation within 1hr",   75,  50,  "%",        "higher_is_better", "WHO BFHI"),
    ("apgar_low_rate",    "Apgar <7 at 5min Rate",      3,   6,   "%",        "lower_is_better",  "NOH Internal"),
    ("pmtct_testing_rate","PMTCT HIV Testing Rate",     95,  85,  "%",        "higher_is_better", "NDoH 95-95-95"),
    ("partograph_rate",   "Partograph Completion Rate",  90,  75,  "%",        "higher_is_better", "NDoH/SOP-003"),
    ("bed_occupancy",     "Labour Ward Occupancy",       80,  95,  "%",        "lower_is_better",  "Healthcare standard"),
    ("competency_rate",   "Staff Competency Compliance", 90,  75,  "%",        "higher_is_better", "NOH Ch.11"),
    ("drill_rate",        "Emergency Drill Completion",  95,  80,  "%",        "higher_is_better", "NOH Ch.12"),
    ("audit_score",       "Clinical Audit Score",        80,  60,  "%",        "higher_is_better", "NOH governance"),
    ("avg_los_nvd",       "Average LOS - NVD",           1.5, 2.5, "days",     "lower_is_better",  "SA private"),
    ("avg_los_cs",        "Average LOS - CS",             3,   4,   "days",     "lower_is_better",  "SA private"),
]


def main():
    print("=" * 60)
    print("NOH Maternity Dashboard — Schema Setup")
    print("=" * 60)
    print()
    print("Copy the SQL below into the Supabase SQL Editor")
    print("(Dashboard > SQL Editor > New Query > Paste > Run)")
    print()
    print("-" * 60)
    print(SQL_SCHEMA)
    print("-" * 60)
    print()

    # Generate KPI target insert SQL
    print("-- Seed KPI targets for all sites")
    sites = ["pta", "jhb", "rus"]
    for site in sites:
        for row in DEFAULT_KPI_TARGETS:
            code, name, green, amber, unit, direction, source = row
            print(
                f"INSERT INTO kpi_targets (site, kpi_code, kpi_name, green_max, amber_max, unit, direction, source) "
                f"VALUES ('{site}', '{code}', '{name}', {green}, {amber}, '{unit}', '{direction}', '{source}') "
                f"ON CONFLICT (site, kpi_code) DO NOTHING;"
            )
    print()
    print("DONE — Run all the above SQL in the Supabase SQL Editor.")


if __name__ == "__main__":
    main()
