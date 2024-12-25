from commands.servers import fetch_servers

def get_final_url(type, entity_id, world, server_code):

    server_info = fetch_servers()
    server_host = next((server['host'] for server in server_info if server['code'] == server_code), None)
    
    if not server_host:
        return ""

    # Replace 'www' with the world identifier in the server host
    host = server_host.replace('www', str(world))
    
    # Determine the URL path based on the type
    if type == "ally":
        return f"https://{host}/game.php?screen=info_ally&id={entity_id}"
    elif type == "player":
        return f"https://{host}/game.php?screen=info_player&id={entity_id}"
    elif type == "village":
        return f"https://{host}/game.php?screen=info_village&id={entity_id}"
    
    # Return an empty string if the type is invalid
    return ""