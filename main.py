import os
import steam_owned_games
from steam_web_api import Steam
from steam_owned_games import fetch_games
from steam_owned_games import fetch_recentlyplayed

KEY = os.environ.get("STEAM_API_KEY")
steam = Steam(KEY)

steam_id = "76561198108372769"  # Example Steam ID
games = fetch_games(steam_id)

if "error" in games:
    print(games["error"])
else:
    for app_id, details in games.items():
        print(f"App ID: {app_id}, Name: {details['Name']}, Playtime: {details['Playtime (Minutes)']} minutes")

print("\n\n\n\n")


games = fetch_recentlyplayed(steam_id)

if "error" in games:
    print(games["error"])
else:
    for app_id, details in games.items():
        print(f"App ID: {app_id}, Name: {details['Name']}, Playtime: {details['Playtime (Minutes)']} minutes")