import os
import shutil
import zipfile
import json
import subprocess
from datetime import datetime

# Configuration
REPO_URL = "https://github.com/skkapilhunters/SecureRoute.git" # Replace with your GitHub URL
BACKUP_DIR = "./backups"
VERSION_FILE = "./version.json"

def run_cmd(command):
    """Executes a system shell command and prints output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error executing '{command}': {result.stderr.strip()}")
        return False
    print(f"✅ {result.stdout.strip()}")
    return True

def save_version_info(tag_or_commit, metadata=None):
    """Saves build details into a version.json file."""
    data = {
        "version": tag_or_commit,
        "deployed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": metadata or {}
    }
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"📝 Version metadata updated: {tag_or_commit}")

def create_package(version_tag):
    """Packages the current bot directory into a versioned zip backup."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    zip_filename = os.path.join(BACKUP_DIR, f"bot_package_{version_tag}.zip")
    
    # Exclude temporary or heavy folders from package
    ignore_dirs = {".git", "__pycache__", "backups", ".venv", "venv"}

    print(f"📦 Packaging bot files into '{zip_filename}'...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, ".")
                zipf.write(filepath, arcname)

    print(f"✅ Package created successfully: {zip_filename}")
    return zip_filename

def update_from_github(branch="main", version_tag="latest"):
    """Clones/Pulls latest code from GitHub, injects version info, and packages it."""
    print("-----------------------------------------------------")
    print(f"[Deploy] Pulling latest updates from GitHub ({branch})...")
    
    # Check if Git repo exists locally
    if os.path.exists(".git"):
        if not run_cmd(f"git fetch origin && git reset --hard origin/{branch}"):
            return False
    else:
        print("[Deploy] Initializing git repository connection...")
        run_cmd(f"git clone {REPO_URL} temp_repo")
        # Copy cloned files over
        for item in os.listdir("temp_repo"):
            if item != ".git":
                s = os.path.join("temp_repo", item)
                d = os.path.join(".", item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        shutil.rmtree("temp_repo")

    # Inject metadata details
    save_version_info(version_tag, {"branch": branch, "status": "deployed"})

    # Pack the version for future rollbacks
    create_package(version_tag)
    
    print("[Deploy] Deployment complete!")
    print("-----------------------------------------------------")
    return True

def restore_backup(version_tag):
    """Restores the bot from a specific version package zip."""
    zip_path = os.path.join(BACKUP_DIR, f"bot_package_{version_tag}.zip")
    if not os.path.exists(zip_path):
        print(f"❌ Backup package '{zip_path}' not found!")
        return False

    print(f"🔄 Restoring bot from package: {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    print("✅ Restore complete! Please restart your bot process.")
    return True

if __name__ == "__main__":
    # Example direct execution:
    # update_from_github(branch="main", version_tag="v1.0.1")
    pass
