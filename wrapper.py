import os
from datetime import datetime
from collections import defaultdict
from steam_web_api import Steam

# Step 1: Set up Steam API key
KEY = os.environ.get("STEAM_API_KEY")
steam = Steam(KEY)

# Step 2: Fetch user friends
def fetch_and_organize_friends(steamid):
    # Fetch friends list from API
    user = steam.users.get_user_friends_list(steamid)
    friends = user["friends"]

    # Step 3: Process the data

    # 1. Sort friends by 'friend_since' (most recent first)
    sorted_friends = sorted(friends, key=lambda x: x["friend_since"], reverse=True)

    # 2. Group by 'personastate'
    grouped_friends = defaultdict(list)
    for friend in sorted_friends:
        grouped_friends[friend.get("personastate", 0)].append(friend)

    # 3. Format data for easier reading
    organized_data = {}
    for state, friends_list in grouped_friends.items():
        organized_data[state] = [
            {
                "Steam ID": friend["steamid"],
                "Name": friend.get("personaname", "Unknown"),
                "Profile URL": friend.get("profileurl", "N/A"),
                "Avatar": friend.get("avatar", "N/A"),
                "Friend Since": datetime.fromtimestamp(friend["friend_since"]).strftime("%Y-%m-%d"),
            }
            for friend in friends_list
        ]

    return organized_data

# Example usage
steamid = "76561198995017863"  # Replace with your desired Steam ID
organized_friends = fetch_and_organize_friends(steamid)

# Print or use the organized data
import json
print(json.dumps(organized_friends, indent=4))
