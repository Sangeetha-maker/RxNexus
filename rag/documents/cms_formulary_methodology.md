# CMS Medicare Part D Formulary & Utilization Methodology Guide

## Overview of Medicare Part D Benefit Design
Medicare Part D prescription drug coverage involves formularies structured into tiers:
- **Tier 1: Preferred Generic**: Lowest cost-sharing for common generic medications.
- **Tier 2: Generic**: Standard generic drugs.
- **Tier 3: Preferred Brand**: Brand-name drugs without generic equivalents on the market, prioritized by the plan.
- **Tier 4: Non-Preferred Drug**: Higher cost-sharing brand and non-preferred generic drugs.
- **Tier 5: Specialty Tier**: High-cost biologic and specialty medications exceeding the CMS specialty threshold ($950+/month).
- **Tier 6: Select Care Drugs**: Specific preventive or chronic care drugs offering $0 or low copays.

## Formulary Utilization Management Restrictions (Friction Points)
Formularies apply clinical guardrails known as utilization management (UM) tools:
1. **Prior Authorization (PA)**: Requires the prescriber to demonstrate clinical necessity before coverage is approved.
2. **Step Therapy (ST)**: Requires trying and failing lower-cost first-line medications (e.g. generic metformin before an SGLT2 inhibitor) before advancing to higher-cost agents.
3. **Quantity Limits (QL)**: Restricts the amount of medication dispensed within a specific timeframe (e.g., 30 tablets per 30 days) to prevent overutilization or waste.

## Payer Opportunity Scoring Methodology
The prototype Opportunity Score combines:
- **Cost Impact (30%)**: Aggregate drug spend and cost per 30-day standardized fill.
- **Utilization (25%)**: Total claim volume and beneficiary exposure.
- **Formulary Friction (20%)**: Combined index of PA, Step Therapy, Quantity Limits, and High Tier barriers.
- **Adherence Risk (15%)**: Synthetically modeled refill gaps and missed possession intervals.
- **Alternative Opportunity (10%)**: Potential for lower-cost generic or preferred-tier review.

## Decision Support Guardrails
PayerRx Optimizer is an analytical decision-support tool. It empowers payer pharmacy directors, clinical pharmacists, and formulary managers with prioritized evidence. It does not replace clinical judgment and never makes autonomous prescription or medication substitution decisions.
