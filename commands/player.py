import re
import aiohttp

async def fetch_player_from_api(player_name, world):
    """
    Fetch player information from the API using their name and the given world.
    """
    base_url = f"https://twhelp.app/api/v2/versions/pt/servers/{world}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/players?limit=1&q={player_name}") as response:
            if response.status == 200:
                data = await response.json()
                if data["data"]:
                    return data["data"][0]
    return None

async def process_player_bbcode(content, world):
    """
    Find BB code for players and replace with a plain link to the player profile.
    """
    player_pattern = r"\[player\](.*?)\[/player\]"
    matches = re.findall(player_pattern, content)

    for match in matches:
        print(f"Processing player: {match}")
        player = await fetch_player_from_api(match, world)
        if player:
            name = player['name']
            profile_url = player["profileUrl"]
            link = f"[{name}]({profile_url})"
            content = content.replace(f"[player]{match}[/player]", link)
        else:
            content = content.replace(
                f"[player]{match}[/player]",
                f"Player '{match}' not found."
            )

    return content
