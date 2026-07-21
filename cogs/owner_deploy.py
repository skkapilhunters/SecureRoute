import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
from deploy_manager import create_in_memory_zip, pull_latest_from_github, get_latest_commit_id

class OwnerDeploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="deploy")
    @commands.is_owner()
    async def deploy_code(self, ctx, version: str = "V 1.0.0"):
        """Zips current code, pulls GitHub updates, and sends a styled Embed with backup."""
        old_commit = get_latest_commit_id()
        status_msg = await ctx.send("📦 **[1/3] Packaging current bot code...**")

        # 1. Create in-memory ZIP backup file
        zip_buffer = create_in_memory_zip()
        backup_filename = f"bot_backup_{old_commit}.zip"
        discord_file = discord.File(fp=zip_buffer, filename=backup_filename)

        # 2. Pull latest code from GitHub
        await status_msg.edit(content="⬇️ **[2/3] Cloning & pulling latest code from GitHub...**")
        new_commit = pull_latest_from_github()

        # 3. Reload cogs
        await status_msg.edit(content="🔄 **[3/3] Applying updates and reloading cogs...**")
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

        # Delete the temporary status message
        await status_msg.delete()

        # Build description string using custom emojis matching your JSON design
        reloaded_cogs_str = ", ".join([f"`{cog}`" for cog in reloaded]) if reloaded else "`None`"
        
        description_text = (
            f"Deployment triggered by {ctx.author.mention}.\n\n"
            f"<a:parrow:1516089889110753383> **Latest Commit :** `{new_commit}`.\n\n"
            f"<a:rarroww:1516090007914287237> **Reloaded Cogs :** {reloaded_cogs_str}.\n\n"
            f"<a:yarrow:1516090009596198963> **Backup Package :** `Commit: {old_commit}`.\n\n"
            f"<a:parrow:1516089889110753383> **Version :** `{version}`.\n\n"
            f"<a:rarroww:1516090007914287237> **File Name :** `{backup_filename}`.\n\n"
            f"<a:wow:1516089962431250473> **System Status :** All modules running & updated!"
        )

        # Create Discord Embed matching your exact theme
        embed = discord.Embed(
            title="<a:bluestar:1529101764450844772> Bot Successfully Updated from GitHub!",
            description=description_text,
            color=43775,  # #00AAFF Cyan/Blue color
            timestamp=datetime.now(timezone.utc)
        )

        avatar_url = self.bot.user.display_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.set_footer(
            text="✧ A-S-R ✧",
            icon_url=avatar_url
        )

        # Send the final embed along with the backup ZIP attachment
        await ctx.send(embed=embed, file=discord_file)

async def setup(bot):
    await bot.add_cog(OwnerDeploy(bot))
