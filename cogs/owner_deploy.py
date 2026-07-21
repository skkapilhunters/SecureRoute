import os
import discord
from discord.ext import commands
from deploy_manager import pull_and_pack_latest

class OwnerDeploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="deploy")
    @commands.is_owner()
    async def deploy_code(self, ctx):
        """Pulls latest GitHub code, zips a backup, and reloads cogs."""
        msg = await ctx.send("⬇️ **[1/2] Cloning & pulling latest code from GitHub...**")
        
        try:
            commit_id = pull_and_pack_latest()
            await msg.edit(content=f"📦 **[2/2] Saved backup ZIP (`backup_{commit_id}.zip`). Reloading cogs...**")

            # Reload all cogs automatically
            reloaded = []
            if os.path.exists("./cogs"):
                for filename in os.listdir("./cogs"):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        cog_name = f"cogs.{filename[:-3]}"
                        await self.bot.reload_extension(cog_name)
                        reloaded.append(filename[:-3])

            await msg.edit(
                content=f"✅ **Bot Successfully Updated from GitHub!**\n"
                        f"• **Latest Commit**: `{commit_id}`\n"
                        f"• **Reloaded Cogs**: `{', '.join(reloaded)}`"
            )
        except Exception as e:
            await msg.edit(content=f"❌ **Deploy Failed:** `{e}`")

async def setup(bot):
    await bot.add_cog(OwnerDeploy(bot))
