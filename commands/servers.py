# commands/servers.py
import requests

def fetch_servers():
    response = requests.get("https://twhelp.app/api/v2/versions?limit=500")
    return response.json()['data'] if response.status_code == 200 else []

def fetch_worlds(server_code):
    url = f"https://twhelp.app/api/v2/versions/{server_code}/servers?limit=500&open=true"
    response = requests.get(url)
    return response.json()['data'] if response.status_code == 200 else []
