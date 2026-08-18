#!/bin/bash
cd /home/site/wwwroot || cd /app || cd .

echo "Working directory is: $(pwd)"
echo "Installing dependencies from requirements.txt..."
python -m pip install --no-cache-dir -r requirements.txt

echo "Starting FastAPI Application via Uvicorn on 0.0.0.0:8000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
