import re
import aiohttp

async def fetch_tribe_from_api(tribe_tag, world):
    """
    Fetch tribe information from the API using the full tribe name by matching the tag and the given world.
    """
    base_url = f"https://twhelp.app/api/v2/versions/pt/servers/{world}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/tribes?limit=100") as response:
            if response.status == 200:
                data = await response.json()
                for tribe in data["data"]:
                    # If the tribe tag matches, return the corresponding tribe info
                    if tribe["tag"].lower() == tribe_tag.lower():  # Case insensitive match
                        return tribe
    return None

async def process_tribe_bbcode(content, world):
    """
    Find BB code for tribes and replace with a plain link to the tribe profile.
    """
    tribe_pattern = r"\[ally\](.*?)\[/ally\]"  # Match tribe tags between [ally] and [/ally]
    matches = re.findall(tribe_pattern, content)

    for match in matches:
        print(f"Processing tribe: {match}")

        # Fetch the tribe information from the API by its tag
        tribe = await fetch_tribe_from_api(match, world)
        if tribe:
            name = tribe['name']
            profile_url = tribe["profileUrl"]
            link = f"[{name}]({profile_url})"
            content = content.replace(f"[ally]{match}[/ally]", link)
        else:
            content = content.replace(f"[ally]{match}[/ally]", f"Tribe '{match}' not found.")

    return content
