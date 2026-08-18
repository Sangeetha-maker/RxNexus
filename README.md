# PayerRx Intelligence

Local-first pharmacy formulary optimization and adherence decision-support prototype for US Medicare Part D payer/pharmacy teams. Every result is **recommended for pharmacist/payer review**; it does not diagnose, prescribe, or substitute medication.

## Included system

- Streaming raw-data inspection, quality reports, curated CSVs, metrics, and scoring in `pipeline.py`.
- Governed data model and crosswalk validation in `models/` and `processing/mapping/`.
- FastAPI evidence and data-quality APIs in `backend/`.
- React executive dashboard and opportunity explorer in `frontend/`.
- Power BI import/mapping assets in `powerbi/`.
- RAG evidence policy, Docker, tests, and portable Azure Container Apps assets.

## Local run

1. Create a Python environment and install: `pip install -r requirements.txt`.
2. Run the complete pipeline: `python pipeline.py`. The supplied CMS utilization file is about 3.8 GB; the full streaming run can take substantial time and disk space. It does not alter raw data.
3. Start the API: `python -m uvicorn backend.main:app --reload --port 8000`.
4. Start the React app: `cd frontend; npm install; npm run dev`.
5. Open the URL printed by Vite (normally `http://localhost:5173`).

Run tests with `python -m pytest tests -q` after installing dependencies.

## Truthful limitations

- CMS Dataset 2 and formulary data are intentionally not joined: no validated crosswalk is present between textual CMS drug names and formulary identifiers, and Synthea IDs do not map to CMS NPI/plan IDs.
- The current score uses only validated CMS cost and utilization signals (60% / 40%). Formulary, adherence, generic, and network factors are not scored until a validated mapping is provided.
- Synthea medication data is labelled synthetic and is kept separate. Its exported prescriptions do not contain sufficient refill/coverage-day detail for defensible PDC/MPR.
- Power BI `.pbix` cannot be programmatically generated reliably in this environment; curated CSVs are ready to import.

## Governed data-model extension

The project now includes a PostgreSQL-compatible serving model in `models/schema.sql`, a controlled drug-crosswalk template, and a validator. An approved crosswalk row requires an authoritative source, confidence, reviewer, and review timestamp before formulary enrichment can be enabled. See `docs/data_model.md`.

## Documentation

Read [architecture](docs/architecture.md), [API reference](docs/api.md), [scoring methodology](docs/scoring_methodology.md), [join strategy](docs/join_strategy.md), [data model](docs/data_model.md), [limitations](docs/limitations.md), [security](docs/security.md), [RAG design](rag/README.md), [Power BI guide](powerbi/README.md), and [Azure deployment](azure/README.md).
