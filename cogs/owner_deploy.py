import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from db_manager import (
    register_bot_config, 
    get_bot_config, 
    update_bot_deployment, 
    get_all_registered_bots
)
from deploy_manager import fetch_repo_and_pack, calculate_smart_version

class MultiBotDeploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_deploy_loop.start() # Starts automatic updates every 6 hours

    def cog_unload(self):
        self.auto_deploy_loop.cancel()

    @commands.command(name="register_bot")
    @commands.is_owner()
    async def register(self, ctx, target_bot: discord.User, repo_url: str, channel: discord.TextChannel):
        """Registers a bot, its repo URL, and its specific backup channel."""
        register_bot_config(
            bot_id=target_bot.id,
            bot_name=target_bot.name,
            repo_url=repo_url,
            channel_id=channel.id
        )
        await ctx.send(f"✅ Successfully registered **{target_bot.name}**!\n"
                       f"• **Repo**: `{repo_url}`\n"
                       f"• **Backup Channel**: {channel.mention}")

    @commands.command(name="deploy")
    @commands.is_owner()
    async def deploy_bot(self, ctx, target_bot: discord.User):
        """Runs target deployment for a specific @bot."""
        config = get_bot_config(target_bot.id)
        if not config:
            await ctx.send(f"❌ **{target_bot.name}** is not registered. Use `!register_bot` first.")
            return

        status_msg = await ctx.send(f"🔄 Processing deployment for **{target_bot.name}**...")
        await self.execute_deployment(config, trigger_ctx=ctx, status_msg=status_msg)

    async def execute_deployment(self, config: dict, trigger_ctx=None, status_msg=None):
        """Core execution logic for both manual and automatic deployments."""
        bot_id = config["bot_id"]
        bot_name = config["bot_name"]
        repo_url = config["repo_url"]
        channel_id = config["channel_id"]
        last_commit = config.get("last_commit", "None")
        last_version = config.get("last_version", "v1.0.0")
        last_deploy_time = config.get("last_deploy_time")

        # 1. Fetch backup channel
        backup_channel = self.bot.get_channel(channel_id)
        if not backup_channel:
            if trigger_ctx:
                await trigger_ctx.send(f"❌ Target backup channel `{channel_id}` not found.")
            return

        # 2. Download repo and pack backup zip
        zip_buffer, new_commit, commit_count = fetch_repo_and_pack(repo_url)

        # Skip if no new commits
        if new_commit == last_commit and trigger_ctx is None:
            return  # Auto-loop skips if code hasn't changed

        # 3. Calculate smart version
        time_diff_hours = 24.0
        if last_deploy_time:
            prev_time = datetime.fromisoformat(last_deploy_time)
            time_diff_hours = (datetime.now(timezone.utc) - prev_time).total_seconds() / 3600.0

        new_version = calculate_smart_version(last_version, commit_count, time_diff_hours)

        # 4. Upload zip file to the bot's dedicated backup channel
        backup_filename = f"{bot_name}_backup_{new_commit}.zip"
        discord_file = discord.File(fp=zip_buffer, filename=backup_filename)

        # Build Embed
        embed = discord.Embed(
            title=f"<a:bluestar:1529101764450844772> {bot_name} Deployment Complete!",
            description=(
                f"<a:parrow:1516089889110753383> **Latest Commit :** `{new_commit}`.\n\n"
                f"<a:rarroww:1516090007914287237> **Previous Commit :** `{last_commit}`.\n\n"
                f"<a:yarrow:1516090009596198963> **Version Issued :** `{new_version}`.\n\n"
                f"<a:parrow:1516089889110753383> **Backup File :** `{backup_filename}`.\n\n"
                f"<a:wow:1516089962431250473> **Status :** Clean Backup & Sync Complete!"
            ),
            color=43775,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="✧ Multi-Bot Deployment System ✧")

        # Send to specific channel
        await backup_channel.send(embed=embed, file=discord_file)

        # 5. Update database record
        now_str = datetime.now(timezone.utc).isoformat()
        update_bot_deployment(bot_id, new_commit, new_version, now_str)

        if status_msg:
            await status_msg.edit(content=f"✅ **{bot_name}** deployed! Backup sent to {backup_channel.mention}.")

    @tasks.loop(hours=6)
    async def auto_deploy_loop(self):
        """Automatically checks for repo updates every 6 hours."""
        print("[Auto-Deploy] Running scheduled check for all bots...")
        bots = get_all_registered_bots()
        for bot_config in bots:
            try:
                await self.execute_deployment(bot_config)
            except Exception as e:
                print(f"[Auto-Deploy Error] Failed for {bot_config.get('bot_name')}: {e}")

    @auto_deploy_loop.before_loop
    async def before_auto_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MultiBotDeploy(bot))
