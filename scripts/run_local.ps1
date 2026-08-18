param([switch]$Pipeline)
$ErrorActionPreference = 'Stop'
if ($Pipeline) { python pipeline.py }
Write-Host 'Start backend: python -m uvicorn backend.main:app --reload --port 8000'
Write-Host 'Start frontend: cd frontend; npm install; npm run dev'
