import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_bot_config(bot_id: str, bot_name: str, repo_url: str, channel_id: int):
    """Registers or updates a bot's deployment configuration."""
    data = {
        "bot_id": str(bot_id),
        "bot_name": bot_name,
        "repo_url": repo_url,
        "channel_id": channel_id,
    }
    # Upsert (insert or update on conflict)
    response = supabase.table("bot_deployments").upsert(data, on_conflict="bot_id").execute()
    return response

def get_bot_config(bot_id: str):
    """Fetches deployment info for a specific bot."""
    response = supabase.table("bot_deployments").select("*").eq("bot_id", str(bot_id)).execute()
    if response.data:
        return response.data[0]
    return None

def update_bot_deployment(bot_id: str, last_commit: str, new_version: str, timestamp_str: str):
    """Updates the commit, version, and deployment timestamp after a deploy."""
    data = {
        "last_commit": last_commit,
        "last_version": new_version,
        "last_deploy_time": timestamp_str
    }
    supabase.table("bot_deployments").update(data).eq("bot_id", str(bot_id)).execute()

def get_all_registered_bots():
    """Gets all registered bots for automated background checks."""
    response = supabase.table("bot_deployments").select("*").execute()
    return response.data if response.data else []
