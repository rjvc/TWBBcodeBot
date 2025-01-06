# commands/building.py
import re
from commands.emojis import EmojiManager

def process_building_bbcode(content: str, emoji_manager: EmojiManager) -> str:
    """Replaces [building] BB codes with corresponding building emojis."""
    def replace_building(match):
        building_name = match.group(1).strip().lower()
        emoji = emoji_manager.get_emoji_string(f"build_{building_name}")
        return emoji if emoji else f"[building]{building_name}[/building]"

    return re.sub(r'\[building\](.*?)\[/building\]', replace_building, content)
