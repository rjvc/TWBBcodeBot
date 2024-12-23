import requests

BASE_URL = "https://twhelp.app/api/v2/versions/pt/servers/pt104"

def fetch_player(name):
    response = requests.get(f"{BASE_URL}/players", params={"q": name, "limit": 1})
    response.raise_for_status()
    return response.json()

def fetch_village(coords):
    response = requests.get(f"{BASE_URL}/villages", params={"coords": coords, "limit": 1})
    response.raise_for_status()
    return response.json()

def fetch_tribe(tribe_id):
    response = requests.get(f"{BASE_URL}/tribes", params={"id": tribe_id, "limit": 1})
    response.raise_for_status()
    return response.json()
