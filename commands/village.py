# commands/village.py
import re
import aiohttp
import urllib.parse
from commands.servers import fetch_servers
from commands.utils import get_final_url

async def fetch_village_from_game(x, y, world, server_code):
    server_info = fetch_servers()
    server_host = next((server['host'] for server in server_info if server['code'] == server_code), None)

    if server_host:
        host = server_host.replace('www', str(world))
        url = f"https://{host}/map/village.txt"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    # Process the data and find the village matching the coordinates
                    for line in data.splitlines():
                        # Split each line by commas
                        village = line.split(",")
                        # Ensure there are enough elements in the village data
                        if len(village) >= 7 and f"{x}|{y}" == f"{village[2]}|{village[3]}":  # Assuming format [x|y]
                           
                            village_name = urllib.parse.unquote(village[1]) 
                            village_name = village_name.replace("+", " ") 
                            return {
                                "id": village[0],
                                "name": village_name,
                                "points": village[5]
                            }
    return None

async def process_village_bbcode(content, world, server_code):
    coord_pattern = r"\[coord\](\d+)\|(\d+)\[/coord\]"
    matches = re.findall(coord_pattern, content)

    for match in matches:
        x, y = match
        # Fetch the village data, using both world and server_code
        village = await fetch_village_from_game(x, y, world, server_code)
        if village:
            village_id = village["id"]
            village_name = village["name"]
            points = village["points"]
            village_url= get_final_url("village", village_id, world, server_code)
            formatted_village = f"[[{village_name}] ({points} points)]({village_url})"

            content = content.replace(f"[coord]{x}|{y}[/coord]", formatted_village)
        else:
            content = content.replace(f"[coord]{x}|{y}[/coord]", f"({x}|{y}) not found.")
    return content