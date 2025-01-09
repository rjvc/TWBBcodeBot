import os
import json
import discord
from discord.ext import commands
from discord.ui import Select, View
from discord import app_commands
from discord import Embed
from dotenv import load_dotenv
from commands.village import process_village_bbcode
from commands.player import process_player_bbcode
from commands.ally import process_tribe_bbcode
from commands.icons import process_unit_bbcode, process_building_bbcode, process_command_bbcode
from commands.servers import fetch_servers, fetch_worlds
from utils.api import fetch_emojis
from commands.emojis import EmojiManager

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APP_ID")
if not TOKEN or not APP_ID:
    raise ValueError("Token or Application ID not found! Make sure 'DISCORD_TOKEN' and 'APP_ID' are set in your .env file.")

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

emoji_manager = EmojiManager(APP_ID, TOKEN)
emoji_manager.load_emojis()

# Fetch app-specific emojis
app_emojis = fetch_emojis(APP_ID, TOKEN)

# Dictionary to store world configurations per channel
channel_configs = {}

def save_configs():
    try:
        with open("channel_configs.json", "w") as f:
            json.dump(channel_configs, f)
    except IOError as e:
        print(f"Error saving configuration: {e}")

def load_configs():
    global channel_configs
    if os.path.exists("channel_configs.json"):
        if os.path.getsize("channel_configs.json") > 0:
            try:
                with open("channel_configs.json", "r") as f:
                    channel_configs = json.load(f)
            except json.JSONDecodeError:
                channel_configs = {}
        else:
            channel_configs = {}
    else:
        channel_configs = {}

# Load the saved configs on startup
load_configs()

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
        select.callback = self.on_server_select
        return select

    async def on_server_select(self, interaction: discord.Interaction):
        self.selected_server = interaction.data['values'][0]
        worlds = fetch_worlds(self.selected_server)
        if not worlds:
            await interaction.response.send_message("No worlds found for this server.", ephemeral=True)
            return

        options = [discord.SelectOption(label=world['key'], value=world['key'])
                   for world in worlds]
        select_world_menu = Select(placeholder="Choose a world", options=options, min_values=1, max_values=1)
        select_world_menu.callback = self.on_world_select
        view = View().add_item(select_world_menu)
        await interaction.response.send_message("Please select a world.", view=view, ephemeral=True)

    async def on_world_select(self, interaction: discord.Interaction):
        selected_world = interaction.data['values'][0]
        channel_id = str(interaction.channel.id)
        channel_configs[channel_id] = {"world": selected_world, "server": self.selected_server}
        save_configs()
        await interaction.response.send_message(f"Server: {self.selected_server}, World: {selected_world} set for this channel.", ephemeral=True)

# Slash command to choose server and world
@tree.command(name="choose", description="Select the server and world for this channel.")
async def choose(interaction: discord.Interaction):
    server_data = fetch_servers()
    if not server_data:
        await interaction.response.send_message("No servers available. Please try again later.", ephemeral=True)
        return

    view = SelectServerWorld(server_data)
    await interaction.response.send_message("Choose a server and world using the dropdown menus below.", view=view, ephemeral=True)

@tree.command(name="check", description="Check the current server and world configuration for this channel.")
async def check(interaction: discord.Interaction):
    """Check the server and world configuration for the current channel."""
    channel_id = str(interaction.channel.id)
    if channel_id in channel_configs:
        config = channel_configs[channel_id]
        server = config.get("server", "Not set")
        world = config.get("world", "Not set")

        # Get host link for the configured server and world
        servers = fetch_servers()
        server_data = next((s for s in servers if s['code'] == server), None)
        if server_data:
            host = server_data.get('host', 'unknown')
            link = f"https://{world}.{host.replace('www.','')}"
        else:
            link = "Unknown (server not found)"

        await interaction.response.send_message(
            f"**Current configuration**\n"
            f"Server: ```{server}```\n"
            f"World: ```{world}```\n"
            f"Link: ```{link}```",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "No server and world configuration is set for this channel. Use /choose to configure it.",
            ephemeral=True
        )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)
    
    # Check if the channel is configured
    if channel_id not in channel_configs:
        await message.channel.send("Please set a world and server using the `/choose` command.")
        return

    # Pre-check for presence of BBCode tags to avoid unnecessary processing
    bbcode_patterns = ['[ally]', '[player]', '[coord]', '[building]', '[unit]', '[command]', '[b]', '[i]', '[u]']
    if not any(pattern in message.content for pattern in bbcode_patterns):
        return  # No BBCode tags found, exit early

    # Retrieve the channel's world configuration
    world_config = channel_configs[channel_id]
    world = world_config['world']
    server_code = world_config['server']
    
    def determine_embed_color(content):
        # Define a mapping of commands to their corresponding colors
        command_colors = {
            "[command]attack[/command]": 0xA9A9A9,  # Light Grey
            "[command]attack_small[/command]": 0x00FF00,  # Green
            "[command]attack_medium[/command]": 0xFFA500,  # Orange
            "[command]attack_large[/command]": 0xFF0000,  # Red
            "[command]support[/command]": 0x0000FF,  # Blue
        }

        # Find matching commands in the content
        matching_commands = [cmd for cmd in command_colors if cmd in content]
        # > 1 command found
        if len(matching_commands) > 1:
            return 0x808080  # Medium Grey
        # 1 command found
        if matching_commands:
            return command_colors[matching_commands[0]]
        # no commands found
        return 0x00FFFF  # Cyan

    
    updated_content = message.content
    updated_content = await process_village_bbcode(updated_content, world, server_code)
    updated_content = await process_player_bbcode(updated_content, world, server_code)
    updated_content = await process_tribe_bbcode(updated_content, world, server_code)
    updated_content = process_unit_bbcode(updated_content, emoji_manager)
    updated_content = process_building_bbcode(updated_content, emoji_manager)
    updated_content = process_command_bbcode(updated_content, emoji_manager)
    updated_content = (
        updated_content
        .replace("[b]", "**").replace("[/b]", "**")
        .replace("[i]", "_").replace("[/i]", "_")
        .replace("[u]", "__").replace("[/u]", "__")
    )
    # Add author mention
    updated_content_with_mention = f"<@{message.author.id}>\n\n{updated_content}"
    embed_color = determine_embed_color(message.content)
    embed = Embed(title=f"{world.upper()}", description=updated_content_with_mention, color=embed_color)

    # Check if content has changed
    if updated_content != message.content:
        try:
            # Create a webhook to send the message as the author
            webhook = await message.channel.create_webhook(name="Formatter Bot")
            
            # Send the embed via webhook
            await webhook.send(
                embed=embed,
                username=message.author.display_name,
                avatar_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url,
            )
            
            # Delete the original message and clean up the webhook
            await message.delete()
            await webhook.delete()

        except Exception as e:
            print(f"An error occurred: {e}")

bot.run(TOKEN)
