# API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Application health and data readiness |
| `GET /api/dashboard` | Aggregate, curated dashboard measures |
| `GET /api/opportunities` | Paginated ranked CMS opportunities; optional `state` filter |
| `GET /api/opportunities/{id}` | Opportunity evidence and review action |
| `GET /api/plans` | Plan records at natural grain |
| `GET /api/pharmacies` | Pharmacy-network records at natural grain |
| `GET /api/synthetic-medications` | Clearly-labelled synthetic medication history |
| `GET /api/quality` | Generated data-quality report |
| `GET /api/data-status` | Curated output availability and row counts |
| `GET /api/limitations` | Safety/data limitations |
| `POST /api/assistant` | Structured evidence summary; no raw-data calculation or clinical advice |

All data endpoints return a `503` with a clear message if the pipeline output is not available.
