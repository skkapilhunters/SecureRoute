import os
import shutil
import zipfile
import subprocess

# Your repository setup
REPO_URL = "https://github.com/skkapilhunters/SecureRoute.git"
BACKUP_DIR = "./backups"

def run_cmd(cmd):
    """Executes shell commands."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None

def get_latest_commit_id():
    """Gets the latest commit ID from GitHub."""
    commit = run_cmd("git rev-parse --short HEAD")
    return commit if commit else "latest"

def auto_zip_backup(commit_id):
    """Zips the current bot folder into backups/ backup_<commit_id>.zip."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    zip_filename = os.path.join(BACKUP_DIR, f"backup_{commit_id}.zip")
    ignore_dirs = {".git", "__pycache__", "backups", ".venv", "venv"}

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, "."))
                
    return zip_filename

def pull_and_pack_latest():
    """Clones/Pulls latest GitHub code and packages a backup automatically."""
    print("[Deploy] Zipping current state before updating...")
    current_commit = get_latest_commit_id()
    auto_zip_backup(current_commit)

    print("[Deploy] Pulling latest code directly from GitHub...")
    if os.path.exists(".git"):
        # Reset local changes and pull latest main branch
        run_cmd("git fetch origin && git reset --hard origin/main")
    else:
        # Clone repo fresh if git isn't initialized
        run_cmd(f"git clone {REPO_URL} temp_repo")
        for item in os.listdir("temp_repo"):
            if item != ".git":
                s, d = os.path.join("temp_repo", item), os.path.join(".", item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        shutil.rmtree("temp_repo")

    new_commit = get_latest_commit_id()
    print(f"[Deploy] Updated to GitHub commit: {new_commit}")
    return new_commit
