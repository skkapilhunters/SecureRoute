import os
import discord
from discord.ext import commands
from deploy_manager import create_in_memory_zip, pull_latest_from_github, get_latest_commit_id

class OwnerDeploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="deploy")
    @commands.is_owner()
    async def deploy_code(self, ctx):
        """Zips current code to Discord channel, pulls GitHub updates, and reloads cogs."""
        old_commit = get_latest_commit_id()
        msg = await ctx.send("📦 **[1/3] Packaging current bot code and uploading to Discord...**")

        # 1. Create in-memory ZIP and send directly to Discord channel
        zip_buffer = create_in_memory_zip()
        discord_file = discord.File(fp=zip_buffer, filename=f"bot_backup_{old_commit}.zip")
        await ctx.send(content=f"📁 **Backup Package (Commit: `{old_commit}`)**", file=discord_file)

        # 2. Pull latest code from GitHub
        await msg.edit(content="⬇️ **[2/3] Cloning & pulling latest code from GitHub...**")
        new_commit = pull_latest_from_github()

        # 3. Reload cogs
        await msg.edit(content="🔄 **[3/3] Applying updates and reloading cogs...**")
        reloaded = []
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and not filename.startswith("__"):
                    cog_name = f"cogs.{filename[:-3]}"
                    await self.bot.reload_extension(cog_name)
                    reloaded.append(filename[:-3])

        await msg.edit(
            content=f"✅ **Bot Successfully Deployed!**\n"
                    f"• **Previous Version Backup**: Uploaded above ⬆️\n"
                    f"• **New GitHub Commit**: `{new_commit}`\n"
                    f"• **Reloaded Cogs**: `{', '.join(reloaded)}`"
        )

async def setup(bot):
    await bot.add_cog(OwnerDeploy(bot))
