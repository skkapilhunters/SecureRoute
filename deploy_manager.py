import os
import shutil
import zipfile
import io
import subprocess
from datetime import datetime, timezone

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else ""

def calculate_smart_version(current_version: str, commits_count: int, time_diff_hours: float):
    """
    Calculates next version based on activity:
    - High activity (>= 3 commits OR changes within < 2 hours): Minor Update (1.0 -> 1.1)
    - Low activity (1-2 commits over longer time): Patch Update (1.0.0 -> 1.0.1)
    """
    if not current_version or not current_version.startswith("v"):
        current_version = "v1.0.0"

    clean_v = current_version.lstrip("v")
    parts = list(map(int, clean_v.split(".")))
    
    while len(parts) < 3:
        parts.append(0)

    major, minor, patch = parts[0], parts[1], parts[2]

    # Rule: 3+ commits OR rapid updates within 2 hours = Minor Update
    if commits_count >= 3 or (time_diff_hours <= 2.0 and commits_count > 1):
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"v{major}.{minor}.{patch}"

def fetch_repo_and_pack(repo_url: str):
    """Clones repo temporarily, zips current code into memory, and pulls updates."""
    temp_dir = "./temp_deploy_repo"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # 1. Clone target repository
    run_cmd(f"git clone {repo_url} {temp_dir}")

    # 2. Extract commit stats
    git_log_count = run_cmd(f"git -C {temp_dir} rev-list --count HEAD")
    commits_count = int(git_log_count) if git_log_count.isdigit() else 1
    
    latest_commit = run_cmd(f"git -C {temp_dir} rev-parse --short HEAD")

    # 3. Create in-memory backup ZIP
    zip_buffer = io.BytesIO()
    ignore_dirs = {".git", "__pycache__", ".venv", "venv"}

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, temp_dir)
                zipf.write(filepath, arcname)

    zip_buffer.seek(0)
    
    # Clean up temp clone directory
    shutil.rmtree(temp_dir)

    return zip_buffer, latest_commit, commits_count
