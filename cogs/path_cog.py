import discord
from discord.ext import commands
from discord import app_commands
from bs4 import BeautifulSoup
import requests
import re
import unicodedata
from googletrans import Translator

# Utility functions
def normalize_text(input_text):
    normalized = unicodedata.normalize("NFD", input_text)
    normalized = normalized.encode("ascii", "ignore").decode("utf-8")
    normalized = re.sub(r"l[’']", "l ", normalized)
    return normalized.lower()

def scrape_chemin_guide(chemin_name):
    formatted_chemin_name = normalize_text(chemin_name).replace(" ", "-")
    website_url = f"https://papycha.fr/chemin-{formatted_chemin_name}/"
    response = requests.get(website_url)
    soup = BeautifulSoup(response.content, "html.parser")
    chemin_guide_content = soup.find("div", class_="entry-content")
    if chemin_guide_content:
        text_content = chemin_guide_content.text.strip()
        image_tags = chemin_guide_content.find_all("img")
        image_urls = [tag["src"] for tag in image_tags]
        return text_content, image_urls
    return None, None

translator = Translator()

async def translate_content(content, language):
    if language not in ["fr", "es", "ar"]:
        return content
    translated = translator.translate(content, dest=language)
    return translated.text

class PathCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="path", description="Retrieve the guide for a specific path.")
    async def path_command(self, interaction: discord.Interaction, path_name: str, language: str = "en"):
        await interaction.response.defer()
        text_content, image_urls = scrape_chemin_guide(path_name)
        if text_content:
            if language != "en":
                text_content = await translate_content(text_content, language)
            chunks = [text_content[i:i+1900] for i in range(0, len(text_content), 1900)]
            for chunk in chunks:
                await interaction.followup.send(chunk)
            for image_url in image_urls:
                await interaction.followup.send(image_url)
        else:
            await interaction.followup.send(f"Path guide for '{path_name}' not found.")

async def setup(bot):
    await bot.add_cog(PathCog(bot))
