import re
import aiohttp

async def fetch_village_from_api(x, y, world):
    """
    Fetch village information from the API using coordinates and the given world.
    """
    base_url = f"https://twhelp.app/api/v2/versions/pt/servers/{world}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/villages?limit=1&coords={x}%7C{y}") as response:
            if response.status == 200:
                data = await response.json()
                if data["data"]:
                    return data["data"][0]
    return None

async def process_village_bbcode(content, world):
    """
    Find BB code for coordinates and replace with a plain link to the village.
    """
    coord_pattern = r"\[coord\](\d+)\|(\d+)\[/coord\]"
    matches = re.findall(coord_pattern, content)

    for match in matches:
        x, y = match
        village = await fetch_village_from_api(x, y, world)
        if village:
            village_name = village["name"]
            profile_url = village["profileUrl"]
            points = village["points"]
            link = f"[{village_name} ({points} pontos)]({profile_url})"
            content = content.replace(f"[coord]{x}|{y}[/coord]", link)
        else:
            content = content.replace(f"[coord]{x}|{y}[/coord]", f"({x}|{y}) not found.")

    return content
