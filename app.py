"""Azure App Service Root Entry Point for RXNexus FastAPI Service.
"""
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
