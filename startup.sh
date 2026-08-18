#!/bin/bash
echo "Installing dependencies from requirements.txt..."
python -m pip install --no-cache-dir -r requirements.txt

echo "Starting FastAPI Application via Uvicorn..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
