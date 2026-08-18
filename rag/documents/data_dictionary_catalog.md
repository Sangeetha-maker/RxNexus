# PayerRx Data Dictionary & Dataset Catalog

## Overview
PayerRx catalogs and harmonizes 33 public federal datasets from the Centers for Medicare & Medicaid Services (CMS) and synthetic clinical cohorts.

## Core Curated Tables & Schema Definitions

### 1. `formulary_drug` (CMS Basic Drugs Formulary)
- **formulary_id**: Unique 8-digit identifier for the Medicare Part D formulary design.
- **rxcui**: RxNorm Concept Unique Identifier representing the clinical drug entity.
- **tier_level**: Assigned cost-sharing tier (Tier 1 Preferred Generic, Tier 2 Generic, Tier 3 Preferred Brand, Tier 4 Non-Preferred, Tier 5 Specialty).
- **prior_authorization_flag**: (1=Yes, 0=No) Requires clinical prior authorization approval before coverage.
- **step_therapy_flag**: (1=Yes, 0=No) Requires trial and failure of preferred lower-cost first-line alternatives.
- **quantity_limit_flag**: (1=Yes, 0=No) Maximum allowed dosage or pill count per 30-day dispensing cycle.
- **formulary_friction_score**: Multi-attribute barrier score (0-100) combining tier penalty, PA, ST, and QL.

### 2. `plan` (Medicare Part D Plan Master)
- **contract_id**: CMS Medicare Advantage or Standalone Part D contract (e.g., H0028, S5820).
- **plan_id**: 3-digit plan package identifier.
- **contract_name**: Sponsor organization legal entity.
- **plan_name**: Marketed consumer plan name.
- **formulary_id**: Linked formulary restriction design.
- **state**: Service area state abbreviation or national coverage indicator.
- **premium**: Monthly beneficiary plan premium in USD.
- **deductible**: Annual prescription drug deductible in USD.

### 3. `beneficiary_cost` (Benefit Phases & Cost Sharing)
- **contract_id**, **plan_id**, **tier_level**: Multi-part foreign keys linking plan tiers.
- **deductible_phase_cost**: Cost-sharing obligation during the annual deductible.
- **initial_coverage_copay**: Fixed dollar copayment during initial coverage (e.g., $0-$47).
- **initial_coverage_coinsurance**: Percentage coinsurance during initial coverage (e.g., 25%-33% for specialty).
- **coverage_gap_pct**: Beneficiary cost-sharing percentage in the coverage gap (standardized at 25% under standard benefit).
- **catastrophic_phase**: Elimination of member cost-sharing in catastrophic phase under the Inflation Reduction Act (IRA).

### 4. `drug_utilization_summary` (CMS Part D Aggregate PUF)
- **brand_name**: Trademarked commercial product name.
- **generic_name**: Active pharmaceutical ingredient (chemical name).
- **total_drug_cost**: Aggregate annual expenditure paid across Part D plans, beneficiaries, and subsidies.
- **total_claims**: Number of 30-day standardized prescription fills and refills.
- **avg_cost_per_claim**: Weighted mean expenditure per standardized 30-day claim.
- **total_beneficiaries**: Unique count of Medicare beneficiaries receiving the medication.

### 5. `pharmacy_network` (CMS Pharmacy Networks)
- **contract_id**: Contract sponsor.
- **pharmacy_number**: NCPDP / NPI pharmacy identifier.
- **pharmacy_zipcode**: 5-digit postal code of pharmacy location.
- **preferred_status_retail**: ('Y'/'N') Preferred retail status offering reduced member copays.
- **preferred_status_mail**: ('Y'/'N') Preferred 90-day mail-order facility.
- **brand_fee_30**: Negotiated 30-day dispensing fee for brand-name prescriptions.
- **generic_fee_30**: Negotiated 30-day dispensing fee for generic prescriptions.
