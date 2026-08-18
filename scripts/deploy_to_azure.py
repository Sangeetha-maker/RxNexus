"""Deploy lightweight curated backend package (<10MB) to Azure App Service."""
import os
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT_DIR / "azure_deploy.zip"

EXCLUDE_PATTERNS = ["venv", ".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".test-deps", ".test-tmp", "node_modules"]

def create_zip():
    print("[1/3] Creating lightweight Azure deploy package (<10 MB)...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Include backend, analytics, models, rag (EXCLUDING any venv/cache)
        for d in ["backend", "analytics", "models", "rag"]:
            dir_path = ROOT_DIR / d
            if dir_path.exists():
                for root, dirs, files in os.walk(dir_path):
                    # Filter out venv directories from traversal
                    dirs[:] = [d_name for d_name in dirs if not any(ex in d_name.lower() for ex in EXCLUDE_PATTERNS)]
                    for file in files:
                        if not file.endswith((".pyc", ".pyo", ".dll", ".pyd")):
                            full_path = Path(root) / file
                            if not any(ex in str(full_path).lower() for ex in EXCLUDE_PATTERNS):
                                arcname = full_path.relative_to(ROOT_DIR)
                                zipf.write(full_path, arcname)

        # 2. Include data/curated only
        curated_dir = ROOT_DIR / "data" / "curated"
        if curated_dir.exists():
            for root, _, files in os.walk(curated_dir):
                for file in files:
                    full_path = Path(root) / file
                    arcname = full_path.relative_to(ROOT_DIR)
                    zipf.write(full_path, arcname)

        # 3. Include top-level files
        for f in ["app.py", "startup.sh", "requirements.txt", ".env"]:
            file_path = ROOT_DIR / f
            if file_path.exists():
                zipf.write(file_path, f)

    size_mb = round(ZIP_PATH.stat().st_size / (1024 * 1024), 2)
    print(f"  * Clean lightweight package created: {ZIP_PATH.name} ({size_mb} MB)")

def deploy_to_azure():
    print("\n[2/3] Uploading and deploying package to Azure App Service (rxnexus-backend-api)...")
    cmd = (
        f'az webapp deploy --resource-group rxnexus-backend '
        f'--name rxnexus-backend-api --src-path "{ZIP_PATH}" --type zip'
    )
    print(f"  Running: {cmd}")
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    print("OUTPUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    print("\n[3/3] Deployment complete! Cleaned up temporary zip.")

if __name__ == "__main__":
    create_zip()
    deploy_to_azure()
