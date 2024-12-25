import re
import aiohttp
import urllib.parse
from commands.servers import fetch_servers
from commands.utils import get_final_url

async def fetch_player_from_game(player_name, world, server_code):
    """
    Fetch player information from the game public files using player name, world, and server_code.
    """
    server_info = fetch_servers()
    server_host = next((server['host'] for server in server_info if server['code'] == server_code), None)

    if server_host:
        host = server_host.replace('www', str(world))
        url = f"https://{host}/map/player.txt"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    for line in data.splitlines():
                        player = line.split(",")  # Use comma as delimiter
                        if len(player) >= 6:  # Ensure sufficient fields
                            # Decode URL-encoded player names
                            decoded_name = urllib.parse.unquote(player[1]).replace("+", " ")
                            if decoded_name.strip().lower() == player_name.strip().lower():
                                return {
                                    "id": player[0],     # Player ID
                                    "name": decoded_name,
                                    "points": player[4], # Points
                                    "rank": player[5]    # Rank
                                }
    return None

async def process_player_bbcode(content, world, server_code):
    """
    Find BBCode for player and replace with a link to the player's profile.
    """
    player_pattern = r"\[player\](.*?)\[/player\]"
    matches = re.findall(player_pattern, content)

    for match in matches:
        player_name = match
        player_data = await fetch_player_from_game(player_name, world, server_code)
        if player_data:
            player_id = player_data["id"]
            player_name = player_data["name"]
            player_url = get_final_url("player", player_id, world, server_code)
            link = f"[[{player_name}]]({player_url})"
            # Replace the BBCode with the formatted link
            content = content.replace(f"[player]{match}[/player]", link)
        else:
            content = content.replace(f"[player]{match}[/player]", f"**{match} not found**")

    return content
