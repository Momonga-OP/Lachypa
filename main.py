import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Retrieve the bot token from the environment variable
bot_token = os.getenv("DISCORD_BOT_TOKEN")
if not bot_token:
    raise ValueError("Bot token is not set in environment variables.")

# Define intents
intents = discord.Intents.default()

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Load all cogs
COGS = ["quest_cog", "path_cog", "super_cog", "me_cog"]

for cog in COGS:
    try:
        bot.load_extension(f"cogs.{cog}")
        logger.info(f"Loaded {cog} cog.")
    except Exception as e:
        logger.error(f"Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(bot_token)
