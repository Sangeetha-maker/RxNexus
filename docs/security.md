# Security and privacy posture

This prototype is local-first. Never commit `.env`, API keys, credentials, raw protected data, or patient-level exports. Restrict CORS through `CORS_ORIGINS`, use HTTPS and identity-aware access in deployment, and keep curated data read-only in the serving container. Before production, conduct data classification, least-privilege access control, audit logging, retention, threat modeling, and applicable HIPAA/compliance reviews.
