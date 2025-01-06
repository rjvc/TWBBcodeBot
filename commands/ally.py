import re
import aiohttp
import urllib.parse
from commands.servers import fetch_servers
from commands.utils import get_final_url

async def fetch_ally_from_game(ally_tag, world, server_code):
    """
    Fetch ally (tribe) information from the game public files using the ally name, world, and server_code.
    """
    server_info = fetch_servers()
    server_host = next((server['host'] for server in server_info if server['code'] == server_code), None)
    
    if server_host:
        host = server_host.replace('www', str(world))
        url = f"https://{host}/map/ally.txt"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    # Process the data and find the ally matching the name
                    for line in data.splitlines():
                        ally = line.split(",")  # Using comma for CSV splitting
                        # Check if the line has the correct number of columns (8 columns)
                        if len(ally) != 8:
                            continue  # Skip lines with incorrect column count
                        # Decode URL-encoded characters in the ally tag
                        ally_tag_decoded = urllib.parse.unquote(ally[2]).replace("+", " ")
                        # Compare the ally tag case-insensitively
                        if ally_tag_decoded.strip().lower() == ally_tag.strip().lower():  # Assuming format [name]
                            return {
                                "id": ally[0],  # Add ally ID
                                "name": ally[1],
                                "tag": ally[2],
                                "points": ally[6],
                                "rank": ally[7]
                            }
    return None

async def process_tribe_bbcode(content, world, server_code):
    """
    Process BBCode of tribe references and format them for Discord.
    """
    # Match the ally tag pattern
    ally_pattern = r"\[ally\](.*?)\[/ally\]"
    matches = re.findall(ally_pattern, content)

    for match in matches:
        ally_data = await fetch_ally_from_game(match, world, server_code)
        if ally_data:
            ally_id = ally_data['id']
            ally_name = ally_data['name'].replace("+", " ")
            ally_url = get_final_url("ally", ally_id, world, server_code)
            formatted_ally = f"[[{ally_name}]]({ally_url})"
            # Replace using the original `match`
            content = content.replace(f"[ally]{match}[/ally]", formatted_ally)
        else:
            # Use the original match in the not-found message
            content = content.replace(f"[ally]{match}[/ally]", f"**Ally: {match} not found**")

    return content


