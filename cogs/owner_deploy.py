import discord
from discord.ext import commands
import sys
import os

# Import the deploy manager functions
from deploy_manager import update_from_github, restore_backup

class OwnerDeploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="deploy")
    @commands.is_owner()
    async def deploy_code(self, ctx, version_tag: str = "latest", branch: str = "main"):
        """Pulls latest GitHub code, creates a zip version package, and reloads cogs."""
        msg = await ctx.send(f"🔄 **[1/3]** Pulling code from branch `{branch}`...")
        
        success = update_from_github(branch=branch, version_tag=version_tag)
        if not success:
            await msg.edit(content="❌ **Deployment failed!** Check server console logs.")
            return

        await msg.edit(content="📦 **[2/3]** Code packaged & saved. Reloading all cogs...")

        # Dynamically reload all cogs in the cogs directory
        reloaded = []
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and not filename.startswith("__"):
                    cog_name = f"cogs.{filename[:-3]}"
                    try:
                        await self.bot.reload_extension(cog_name)
                        reloaded.append(filename[:-3])
                    except Exception as e:
                        print(f"Failed to reload {cog_name}: {e}")

        await msg.edit(
            content=f"✅ **[3/3] Successfully Deployed!**\n"
                    f"• **Version Tag**: `{version_tag}`\n"
                    f"• **Reloaded Cogs**: `{', '.join(reloaded)}`"
        )

    @commands.command(name="rollback")
    @commands.is_owner()
    async def rollback_code(self, ctx, version_tag: str):
        """Restores a previous packaged version zip."""
        await ctx.send(f"🔄 Attempting rollback to version package: `{version_tag}`...")
        
        if restore_backup(version_tag):
            await ctx.send("✅ Backup restored! Restarting bot process...")
            # Automatically restarts the python script process
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            await ctx.send("❌ Rollback failed. Package does not exist.")

async def setup(bot):
    await bot.add_cog(OwnerDeploy(bot))
