# Medicare Part D Plan Architecture & Beneficiary Cost-Sharing

## Medicare Part D Benefit Design
Medicare Part D plans are offered by private health plans approved by CMS. Plans are structured around:
- **Premiums**: Monthly fixed payments by beneficiaries.
- **Annual Deductible**: The initial amount members must pay out-of-pocket before insurance coverage begins (standard limit defined annually by CMS).

## Four Benefit Phases
1. **Deductible Phase**: Beneficiary pays 100% of prescription costs up to the deductible threshold.
2. **Initial Coverage Phase**: Plan and beneficiary share costs based on assigned formulary tiers (copayments for Tier 1-3, coinsurance for Tier 4-5).
3. **Coverage Gap (Donut Hole)**: Beneficiary pays 25% for brand and generic medications.
4. **Catastrophic Coverage Phase**: Under the Inflation Reduction Act (IRA), beneficiary coinsurance is eliminated ($0 out-of-pocket) once reaching the catastrophic threshold.

## Cost-Sharing by Formulary Tier
- **Tier 1 (Preferred Generic)**: Lowest copay ($0 - $5) to encourage first-line generic utilization.
- **Tier 2 (Generic)**: Low copay ($5 - $15) for standard generic formulations.
- **Tier 3 (Preferred Brand)**: Moderate copay ($35 - $47) for brand drugs with negotiated rebates and no direct generic substitute.
- **Tier 4 (Non-Preferred Drug)**: Higher coinsurance (35% - 50%) to steer utilization toward preferred agents.
- **Tier 5 (Specialty Tier)**: High coinsurance (25% - 33%) for high-cost biologic or specialty therapies exceeding the CMS monthly threshold.
