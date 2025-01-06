import re
from commands.emojis import EmojiManager

def process_unit_bbcode(content: str, emoji_manager: EmojiManager) -> str:
    """Replaces [unit] BB codes with corresponding unit emojis."""
    
    emoji_manager.load_emojis()

    def replace_unit(match):
        unit_name = match.group(1).strip().lower()  # Get unit name and convert to lowercase
        # print(f"Processing unit: {unit_name}")  # Debugging print
        emoji = emoji_manager.get_emoji_string(f"unit_{unit_name}")  # Fetch emoji by name
        # print(f"Emoji for {unit_name}: {emoji}")  # Debugging print
        return emoji if emoji else f"[unit]{unit_name}[/unit]"  # Fallback to BBCode if no emoji found

    # Match [unit] tags and replace them with emojis
    result = re.sub(r'\[unit\](.*?)\[/unit\]', replace_unit, content)
    # print(f"Processed content: {result}")  # Debugging print

    return result

def process_building_bbcode(content: str, emoji_manager: EmojiManager) -> str:
    """Replaces [building] BB codes with corresponding building emojis."""
    def replace_building(match):
        building_name = match.group(1).strip().lower()
        emoji = emoji_manager.get_emoji_string(f"build_{building_name}")
        return emoji if emoji else f"[building]{building_name}[/building]"

    return re.sub(r'\[building\](.*?)\[/building\]', replace_building, content)

def process_command_bbcode(content: str, emoji_manager: EmojiManager) -> str:
    """Replaces [command] BB codes with corresponding command emojis."""
    def replace_command(match):
        command_name = match.group(1).strip().lower()  # Extract command name
        emoji = emoji_manager.get_emoji_string(command_name)  # Fetch emoji by name
        return emoji if emoji else f"[command]{command_name}[/command]"  # Fallback to BBCode if emoji not found
    
    # Match [command] tags and replace them with emojis
    return re.sub(r'\[command\](.*?)\[/command\]', replace_command, content)
