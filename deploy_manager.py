import os
import shutil
import zipfile
import io
import subprocess

REPO_URL = "https://github.com/skkapilhunters/SecureRoute.git"

def run_cmd(cmd):
    """Executes shell commands safely."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None

def get_latest_commit_id():
    """Gets the latest commit ID from Git."""
    commit = run_cmd("git rev-parse --short HEAD")
    return commit if commit else "latest"

def create_in_memory_zip():
    """Zips the bot files directly into memory without saving to disk."""
    zip_buffer = io.BytesIO()
    ignore_dirs = {".git", "__pycache__", ".venv", "venv"}

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, "."))

    zip_buffer.seek(0)
    return zip_buffer

def pull_latest_from_github():
    """Clones/Pulls the absolute latest code directly from GitHub."""
    print("[Deploy] Pulling latest code directly from GitHub...")
    if os.path.exists(".git"):
        run_cmd("git fetch origin && git reset --hard origin/main")
    else:
        run_cmd(f"git clone {REPO_URL} temp_repo")
        for item in os.listdir("temp_repo"):
            if item != ".git":
                s, d = os.path.join("temp_repo", item), os.path.join(".", item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        shutil.rmtree("temp_repo")

    return get_latest_commit_id()
