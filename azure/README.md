# Portable Azure deployment

Azure is a hosting target only. Run ETL locally, produce curated CSVs, and test the API before packaging. Do not deploy protected or patient-level data without security, compliance, and data-access approval.

1. Build and publish `backend/` and `frontend/` Docker images to a registry.
2. Create a resource group and run `./deploy.ps1 -ResourceGroup <rg> -ApiImage <image> -WebImage <image> -CorsOrigins https://<web-domain>`.
3. Mount or otherwise provide the read-only curated `data/` outputs to the API container; the Bicep file does not introduce Azure storage as an application dependency.
4. Verify `https://<api-domain>/health`, then configure the frontend build with that API URL and set precise CORS origins.

Container Apps consumption pricing depends on requests, CPU/memory, and egress. Use zero-to-one replica scaling for this demo; production needs capacity, observability, secret management, access control, and compliance review.
