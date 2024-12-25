# main.py
import os
import discord
import json
from discord.ext import commands
from discord.ui import Select, View
from discord import app_commands
from discord import *
from dotenv import load_dotenv
from commands.village import process_village_bbcode
from commands.player import process_player_bbcode
from commands.tribe import process_tribe_bbcode
from commands.servers import fetch_servers, fetch_worlds  # Correct path to 'servers.py' inside 'commands' directory

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

# Select Menu for Server and World selection
class SelectServerWorld(View):
    def __init__(self, server_data):
        super().__init__()
        self.server_data = server_data
        self.selected_server = None
        self.add_item(self.create_server_select_menu())

    def create_server_select_menu(self):
        # Creating the select menu for server selection
        options = [discord.SelectOption(label=server['name'], value=server['code'])
                   for server in self.server_data]
        select = Select(placeholder="Choose a server", options=options, min_values=1, max_values=1)
        select.callback = self.on_server_select  # Set the callback for when a server is selected
        return select

    async def on_server_select(self, interaction: discord.Interaction):
        """Handle server selection."""
        # Store the selected server from the interaction
        self.selected_server = interaction.data['values'][0]
        # Fetch worlds based on the selected server
        worlds = fetch_worlds(self.selected_server)
        if not worlds:
            await interaction.response.send_message("No worlds found for this server.")
            return

        # Prepare the dropdown menu with the fetched worlds
        options = [discord.SelectOption(label=world['key'], value=world['key'])
                   for world in worlds]

        # Create the select menu for world selection
        select_world_menu = Select(placeholder="Choose a world", options=options, min_values=1, max_values=1)
        select_world_menu.callback = self.on_world_select  # Set the callback for when a world is selected

        # Create a new View and add the world select menu
        view = View().add_item(select_world_menu)
        await interaction.response.send_message("Please select a world.", view=view)

    async def on_world_select(self, interaction: discord.Interaction):
        """Handle world selection."""
        # Store the selected world from the interaction
        selected_world = interaction.data['values'][0]
        channel_id = str(interaction.channel.id)

        # Save the selected world and server to the channel configuration
        channel_configs[channel_id] = {"world": selected_world, "server": self.selected_server}
        save_configs()  # Save the updated configurations

        await interaction.response.send_message(f"Server: {self.selected_server}, World: {selected_world} set for this channel.")


# Event for when a message is received
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)

    if channel_id not in channel_configs:
        await message.channel.send("Please set a world and server using the command !twbb set [server] [world].")
        return

    world_config = channel_configs.get(channel_id)
    world = world_config['world']
    server_code = world_config['server']

    # Process BBcode for villages, players, and tribes
    updated_content = message.content
    updated_content = await process_village_bbcode(updated_content, world, server_code)
    updated_content = await process_player_bbcode(updated_content, world, server_code)
    updated_content = await process_tribe_bbcode(updated_content, world, server_code)

    await message.reply(updated_content)

# Command to set world and server configuration for the channel
@bot.command()
async def set(ctx, server: str, world: str):
    """Set the world and server for the current channel."""
    channel_configs[str(ctx.channel.id)] = {"world": world, "server": server}
    save_configs()
    await ctx.send(f"World: {world} and server: {server} set for this channel.")

# Run the bot
bot.run(TOKEN)
