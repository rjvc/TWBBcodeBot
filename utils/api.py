# utils/api.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APP_ID")
if not TOKEN or not APP_ID:
    raise ValueError("Token or Application ID not found! Make sure 'DISCORD_TOKEN' and 'APP_ID' are set in your .env file.")

def fetch_emojis(APP_ID, TOKEN):
    if not APP_ID or not TOKEN:
        raise ValueError("App ID and Token must be provided.")
    
    url = f"https://discord.com/api/v10/applications/{APP_ID}/emojis"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "content-type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            emojis_data = response.json()  # Convert the response to JSON
            # emoji data is inside the "items" key
            emojis = emojis_data.get('items', [])
            if not emojis:
                print("No emojis found in response.")
                return []

            # Extract only 'id' and 'name' from each emoji
            emojis = [{"id": emoji["id"], "name": emoji["name"]} for emoji in emojis]
#            print(f"Processed emojis: {emojis}")  # Debugging print to check the extracted emoji list
            return emojis
        
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response content: {response.text}")
            raise 
    else:
        raise Exception(f"Failed to fetch emojis: {response.status_code} {response.text}")

