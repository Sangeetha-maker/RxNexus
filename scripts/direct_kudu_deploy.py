"""Direct Azure Kudu ZipDeploy using Azure CLI Bearer OAuth Token."""
import os
import zipfile
import subprocess
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT_DIR / "direct_kudu_deploy.zip"

EXCLUDE_PATTERNS = ["venv", ".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".test-deps", ".test-tmp", "node_modules"]

def get_bearer_token():
    cmd = "az account get-access-token --query accessToken -o tsv"
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return res.stdout.strip()

def create_zip():
    print("[1/3] Packaging clean lightweight application...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for d in ["backend", "analytics", "models", "rag"]:
            dir_path = ROOT_DIR / d
            if dir_path.exists():
                for root, dirs, files in os.walk(dir_path):
                    dirs[:] = [d_name for d_name in dirs if not any(ex in d_name.lower() for ex in EXCLUDE_PATTERNS)]
                    for file in files:
                        if not file.endswith((".pyc", ".pyo", ".dll", ".pyd")):
                            full_path = Path(root) / file
                            if not any(ex in str(full_path).lower() for ex in EXCLUDE_PATTERNS):
                                arcname = full_path.relative_to(ROOT_DIR)
                                zipf.write(full_path, arcname)

        curated_dir = ROOT_DIR / "data" / "curated"
        if curated_dir.exists():
            for root, _, files in os.walk(curated_dir):
                for file in files:
                    full_path = Path(root) / file
                    arcname = full_path.relative_to(ROOT_DIR)
                    zipf.write(full_path, arcname)

        for f in ["app.py", "startup.sh", "requirements.txt", ".env"]:
            file_path = ROOT_DIR / f
            if file_path.exists():
                zipf.write(file_path, f)

    size_mb = round(ZIP_PATH.stat().st_size / (1024 * 1024), 2)
    print(f"  * Zip package created: {ZIP_PATH.name} ({size_mb} MB)")

def deploy_kudu_oauth():
    print("\n[2/3] Getting Azure OAuth Bearer Token and uploading to Kudu...")
    token = get_bearer_token()
    if not token:
        print("  Failed to get access token from az CLI.")
        return

    url = "https://rxnexus-backend-api-akbye6ehcffydqb7.scm.southeastasia-01.azurewebsites.net/api/zipdeploy"
    print(f"  Uploading 6.5MB package to: {url}")

    with open(ZIP_PATH, "rb") as f:
        data = f.read()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/octet-stream")
    req.add_header("Content-Length", str(len(data)))

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            print(f"  Response Status: {response.status} {response.reason}")
            print("  Successfully uploaded and deployed to /home/site/wwwroot/!")
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  Error: {e}")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    print("\n[3/3] Deployment complete!")

if __name__ == "__main__":
    create_zip()
    deploy_kudu_oauth()
