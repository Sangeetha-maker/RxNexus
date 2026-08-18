-- PayerRx Intelligence logical serving model (PostgreSQL compatible).
-- This schema stores curated facts and governed mapping decisions; it does not store raw data.

CREATE TABLE IF NOT EXISTS processing_run (
  processing_run_id UUID PRIMARY KEY,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  pipeline_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','complete','failed'))
);

CREATE TABLE IF NOT EXISTS source_file (
  source_file_id BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  source_dataset TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  source_format TEXT NOT NULL,
  original_row_count BIGINT,
  parsed_row_count BIGINT,
  rejected_row_count BIGINT NOT NULL DEFAULT 0,
  UNIQUE (processing_run_id, relative_path)
);

CREATE TABLE IF NOT EXISTS drug_crosswalk (
  drug_crosswalk_id BIGSERIAL PRIMARY KEY,
  source_system TEXT NOT NULL CHECK (source_system IN ('CMS_Dataset_2','CMS_Formulary','Synthea','DLSum')),
  source_drug_identifier TEXT,
  source_drug_name TEXT,
  source_generic_name TEXT,
  target_rxcui TEXT,
  target_ndc TEXT,
  match_method TEXT NOT NULL CHECK (match_method IN ('exact_rxcui','exact_ndc','authoritative_reference','manual_review')),
  authoritative_source TEXT NOT NULL,
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  review_status TEXT NOT NULL CHECK (review_status IN ('pending','approved','rejected','retired')),
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ,
  notes TEXT,
  CHECK (target_rxcui IS NOT NULL OR target_ndc IS NOT NULL),
  CHECK ((review_status = 'approved' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL) OR review_status <> 'approved')
);
CREATE UNIQUE INDEX IF NOT EXISTS drug_crosswalk_natural_key
  ON drug_crosswalk(source_system, source_drug_identifier, source_drug_name, target_rxcui, target_ndc);

-- CMS fact stays at PRESCRIBER x DRUG natural grain.
CREATE TABLE IF NOT EXISTS fact_prescriber_drug (
  prescriber_drug_id BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  prescriber_npi TEXT NOT NULL,
  brand_name TEXT,
  generic_name TEXT,
  total_claims NUMERIC,
  total_30day_fills NUMERIC,
  total_drug_cost NUMERIC,
  total_beneficiaries NUMERIC,
  cost_per_claim NUMERIC,
  cost_per_beneficiary NUMERIC,
  source_drug_identifier TEXT,
  UNIQUE(processing_run_id, prescriber_npi, brand_name, generic_name)
);

-- Formulary fact stays at FORMULARY x drug identifier grain.
CREATE TABLE IF NOT EXISTS fact_formulary_drug (
  formulary_drug_id BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  formulary_id TEXT NOT NULL,
  formulary_version TEXT,
  rxcui TEXT,
  ndc TEXT,
  tier_level NUMERIC,
  prior_authorization TEXT,
  step_therapy TEXT,
  quantity_limit TEXT,
  selected_drug TEXT,
  CHECK (rxcui IS NOT NULL OR ndc IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS dim_plan (
  plan_key BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  contract_id TEXT,
  plan_id TEXT,
  segment_id TEXT,
  plan_year INTEGER,
  UNIQUE(processing_run_id, contract_id, plan_id, segment_id, plan_year)
);

CREATE TABLE IF NOT EXISTS fact_pharmacy_network (
  pharmacy_network_id BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  plan_id TEXT,
  pharmacy_id TEXT,
  network_status TEXT,
  preferred_status TEXT,
  state TEXT,
  county TEXT
);

-- Synthetic data remains a distinct domain. There is intentionally no FK to CMS facts.
CREATE TABLE IF NOT EXISTS fact_synthetic_medication_history (
  synthetic_medication_id BIGSERIAL PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  synthetic_patient_id TEXT NOT NULL,
  medication_code TEXT,
  medication_description TEXT,
  medication_start_at TIMESTAMPTZ,
  medication_stop_at TIMESTAMPTZ,
  age_at_medication NUMERIC,
  synthetic_patient_data BOOLEAN NOT NULL DEFAULT TRUE CHECK (synthetic_patient_data = TRUE)
);

CREATE TABLE IF NOT EXISTS fact_opportunity (
  opportunity_id TEXT PRIMARY KEY,
  processing_run_id UUID REFERENCES processing_run(processing_run_id),
  prescriber_drug_id BIGINT REFERENCES fact_prescriber_drug(prescriber_drug_id),
  opportunity_score NUMERIC NOT NULL CHECK (opportunity_score BETWEEN 0 AND 100),
  opportunity_priority TEXT NOT NULL CHECK (opportunity_priority IN ('Critical','High','Medium','Low')),
  cost_score NUMERIC NOT NULL,
  utilization_score NUMERIC NOT NULL,
  formulary_score NUMERIC,
  network_score NUMERIC,
  generic_score NUMERIC,
  adherence_score NUMERIC,
  mapping_status TEXT NOT NULL CHECK (mapping_status IN ('not_applicable','unmapped','approved')),
  recommended_review_action TEXT NOT NULL
);
