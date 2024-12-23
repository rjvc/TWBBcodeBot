import os
import discord
from discord.ext import commands
from discord.ui import Select, View
from discord import app_commands
import requests
import json
from dotenv import load_dotenv
from commands.village import process_village_bbcode
from commands.player import process_player_bbcode
from commands.tribe import process_tribe_bbcode

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Token not found! Make sure 'DISCORD_TOKEN' is set in your .env file.")

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!twbb ", intents=intents)

# Dictionary to store world configurations per channel
channel_configs = {}

# Helper function to save channel config to a file (optional, can be replaced by DB)
def save_configs():
    try:
        with open("channel_configs.json", "w") as f:
            json.dump(channel_configs, f)
            print("Configuration saved successfully.")  # Debugging line
    except IOError as e:
        print(f"Error saving configuration: {e}")

def load_configs():
    global channel_configs
    if os.path.exists("channel_configs.json"):
        print("Loading configuration from channel_configs.json")  # Debugging line
        if os.path.getsize("channel_configs.json") > 0:
            try:
                with open("channel_configs.json", "r") as f:
                    channel_configs = json.load(f)
            except json.JSONDecodeError:
                channel_configs = {}
                print("Warning: Config file is invalid. Using defaults.")
        else:
            channel_configs = {}
            print("Warning: Config file is empty. Using defaults.")
    else:
        channel_configs = {}
        print("Warning: Config file not found. Using defaults.")

# Load the saved configs on startup
load_configs()

# Helper functions to fetch servers and worlds from the API
def fetch_servers():
    response = requests.get("https://twhelp.app/api/v2/versions?limit=500")
    return response.json()['data'] if response.status_code == 200 else []

def fetch_worlds(server_code):
    url = f"https://twhelp.app/api/v2/versions/{server_code}/servers?limit=500&open=true"
    response = requests.get(url)
    return response.json()['data'] if response.status_code == 200 else []

# Select Menu for Server and World selection
class SelectServerWorld(View):
    def __init__(self, server_data):
        super().__init__()
        self.server_data = server_data
        self.selected_server = None
        self.add_item(self.create_server_select_menu())

    def create_server_select_menu(self):
        options = [discord.SelectOption(label=server['name'], value=server['code'])
                   for server in self.server_data]
        select = Select(placeholder="Choose a server", options=options, min_values=1, max_values=1)
        select.callback = self.on_server_select  # Ensure the callback is set properly here
        return select

    async def on_server_select(self, interaction: discord.Interaction):
        """Handle server selection."""
        self.selected_server = interaction.data['values'][0]
        worlds = fetch_worlds(self.selected_server)  # No need to await this, it's a synchronous function
        if worlds:
            options = [discord.SelectOption(label=world['key'], value=world['key'])
                       for world in worlds]
            select_world_menu = Select(placeholder="Choose a world", options=options, min_values=1, max_values=1)
            select_world_menu.callback = self.on_world_select
            view = View().add_item(select_world_menu)  # Create a new View instance
            await interaction.response.send_message("Please select a world.", view=view)
        else:
            await interaction.response.send_message("No worlds found for this server.")

    async def on_world_select(self, interaction: discord.Interaction):
        """Handle world selection."""
        selected_world = interaction.data['values'][0]
        channel_id = str(interaction.channel.id)
        channel_configs[channel_id] = {"world": selected_world, "server": self.selected_server}  # Save selected world and server
        save_configs()  # Save config to file
        await interaction.response.send_message(f"You have selected world `{selected_world}` for server `{self.selected_server}` in this channel.")

# Register the slash command to choose server/world
@bot.tree.command(name="choose", description="Choose a server and world for this channel")
async def choose(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)

    # Check if a world is already set for this channel
    if channel_id in channel_configs and "world" in channel_configs[channel_id]:
        # Inform the user of the current world and server
        current_world = channel_configs[channel_id]['world']
        current_server = channel_configs[channel_id]['server']
        await interaction.response.send_message(
            f"This channel already has a world set (`{current_world}` for server `{current_server}`).\n"
            "If you want to change it, you can choose a new world from the list below."
        )

        # Wait for a moment and then show the server/world dropdown menu
        await interaction.followup.send("Please select a server:", view=SelectServerWorld(fetch_servers()))

    else:
        # If no world is set, trigger the world selection process
        servers = fetch_servers()
        if servers:
            select_view = SelectServerWorld(servers)
            await interaction.response.send_message("Please select a server:", view=select_view)
        else:
            await interaction.response.send_message("Could not fetch servers at the moment.")

# Register the slash command to show available servers
@bot.tree.command(name="servers", description="Show the available servers")
async def servers(interaction: discord.Interaction):
    """Fetches and displays available servers."""
    servers = fetch_servers()
    if servers:
        embed = discord.Embed(title="Available Servers", description="Here are the available servers:", color=discord.Color.blue())
        for server in servers:
            country_code = server.get("code")  # Country code (e.g., 'br' for Brazil)
            country_flag = f":flag_{country_code.lower()}:"  # Display flag emoji
            embed.add_field(name=f"{country_flag} {server['name']}", value=f"Server Code: {server['code']}", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Couldn't fetch server information at the moment.")

# Register the slash command to show the world list based on server code
@bot.tree.command(name="worlds", description="Show the available worlds for a specific server")
async def worlds(interaction: discord.Interaction, server_code: str):
    """Fetches and displays open worlds for a specific server."""
    worlds = fetch_worlds(server_code)
    if worlds:
        embed = discord.Embed(title=f"Available Worlds for {server_code.upper()}", description="Here are the open worlds:", color=discord.Color.green())
        for world in worlds:
            key = world.get("key")
            embed.add_field(name=key, value=f"World Key: {key}", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"Couldn't fetch world information for server {server_code.upper()}.")

# Event listener to sync slash commands
@bot.event
async def on_ready():
    # Sync commands with Discord
    await bot.tree.sync()
    print(f"Bot is ready and slash commands are synced.")

# Event listener for messages
@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Process the command
    await bot.process_commands(message)

    channel_id = str(message.channel.id)
    world = channel_configs.get(channel_id, {}).get("world")

    if not world:
        # If no world is set, trigger the world selection process
        await message.channel.send("This channel does not have a world configured yet. Use `/choose` to set one.")
        return

    content = message.content
    updated_content = content

    # Process BB codes with the dynamic world
    updated_content = await process_village_bbcode(updated_content, world)
    updated_content = await process_player_bbcode(updated_content, world)
    updated_content = await process_tribe_bbcode(updated_content, world)

    # If the content was updated, send the updated response
    if updated_content != content:
        await message.reply(updated_content)

# Start the bot
bot.run(TOKEN)
