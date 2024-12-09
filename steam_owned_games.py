import os
from steam_web_api import Steam

KEY = os.environ.get("STEAM_API_KEY")
steam = Steam(KEY)

def fetch_games(steam_id):
    """
    Fetches owned games for the given Steam ID and returns the information as a dictionary.

    Args:
        steam_id (str): The Steam ID to fetch games for.

    Returns:
        dict: A dictionary containing game information.
    """
    # Fetch owned games
    user = steam.users.get_owned_games(steam_id)

    # Check if the response contains games
    if "games" not in user:
        return {"error": "No games found or response is invalid."}

    # Create a dictionary with the games data
    games_info = {
        game["appid"]: {
            "Name": game.get("name", "Unknown Game"),
            "Playtime (Minutes)": game["playtime_forever"],
        }
        for game in user["games"]
    }

    return games_info

def fetch_recentlyplayed(steam_id):
    """
    Fetches recently played games for the given Steam ID and returns the information as a dictionary.

    Args:
        steam_id (str): The Steam ID to fetch games for.

    Returns:
        dict: A dictionary containing game information.
    """
    # Fetch owned games
    user = steam.users.get_user_recently_played_games(steam_id)

    # Check if the response contains games
    if "games" not in user:
        return {"error": "No games found or response is invalid."}

    # Create a dictionary with the games data
    games_info = {
        game["appid"]: {
            "Name": game.get("name", "Unknown Game"),
            "Playtime (Minutes)": game["playtime_forever"],
        }
        for game in user["games"]
    }

    return games_info