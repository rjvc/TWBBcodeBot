# commands/emojis.py

from utils.api import fetch_emojis

# commands/emojis.py

class EmojiManager:
    def __init__(self, app_id, token):
        self.app_id = app_id
        self.token = token
        self.emojis = []

    def load_emojis(self, force_reload=False):
        """Fetch emojis using the API and load them into the manager."""
        if not self.emojis or force_reload:
            try:
                self.emojis = fetch_emojis(self.app_id, self.token)

                # Check if the emojis are dictionaries with 'name' and 'id'
                for emoji in self.emojis:
                    if not isinstance(emoji, dict) or 'name' not in emoji or 'id' not in emoji:
                        raise ValueError("Invalid emoji format.")
                    
            except Exception as e:
                print(f"Error fetching emojis: {e}")
                self.emojis = []

    def get_emoji_id(self, name):
        """Find the ID of an emoji by its name."""
        if not self.emojis:
            self.load_emojis()

        for emoji in self.emojis:
            if emoji['name'] == name:
                return emoji['id']
        return None

    def get_emoji_string(self, name):
        """Create the string representation of an emoji for Discord messages."""
        emoji_id = self.get_emoji_id(name)
        if emoji_id:
            return f"<:{name}:{emoji_id}>"
        else:
            return f"Emoji not found for {name}"  # Provide feedback if no emoji found
