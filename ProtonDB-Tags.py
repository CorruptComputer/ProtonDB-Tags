#!/usr/bin/env python3

import argparse
import os
import sys
import time
import vdf
import requests

from Utils.CacheManager import CacheManager
from Utils.ConfigManager import ConfigManager


class ProtonDBError(Exception):
    pass

class SteamApiError(Exception):
    pass


###############################################################################
#    Checks if the game has Native Linux support from the Steam Store API     #
# app_id: (str) The steam application id to check                             #
# return: (boolean) If the game is native                                     #
###############################################################################
def is_native(app_id):
    cache_manager = CacheManager()
    (found_in_cache, value) = cache_manager.get_from_steam_native_cache(app_id)
    if found_in_cache:
        return value

    # Thanks to u/FurbyOnSteroid for finding this!
    # https://www.reddit.com/r/linux_gaming/comments/bxqsvs/protondb_to_steam_library_tool/eqal68r/
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=platforms"
    steam_api_result = requests.get(api_url)
    # Wait 1.3 seconds before continuing, as Steam only allows 10 requests per 10 seconds, otherwise you get rate limited for a few minutes.
    time.sleep(1.3)

    if steam_api_result.status_code != 200:
        print(f"Error pulling info from Steam API for {app_id}. You're probably being rate-limited or the store page no longer exists.")
        return False

    steam_api_json = steam_api_result.json()

    # If steam can't find the game it will be False
    if steam_api_json[app_id]["success"] in ["True", "true", True]:
        is_native_game = steam_api_json[app_id]["data"]["platforms"]["linux"] in ["True", "true", True]
        cache_manager.add_to_steam_native_cache(app_id, is_native_game)

        return is_native_game

    return False

###############################################################################
#   Checks which ConfigStore you have, some are Local and some are Roaming    #
# sharedconfig: (dict) The vdf dict to check                                  #
# fetch_games: (bool) Should games be checked from Steam API?                 #
# return: (dict) The apps list to run the checks on                           #
###############################################################################
def get_apps_list(sharedconfig, fetch_games):
    configstore_keys = ["UserLocalConfigStore", "UserRoamingConfigStore"]
    for key in configstore_keys:
        if key in sharedconfig:
            configstore = key

    software_keys = ["software", "Software"]
    for key in software_keys:
        if key in sharedconfig[configstore]:
            software = key

    valve_keys = ["valve", "Valve"]
    for key in valve_keys:
        if key in sharedconfig[configstore][software]:
            valve = key

    steam_keys = ["steam", "Steam"]
    for key in steam_keys:
        if key in sharedconfig[configstore][software][valve]:
            steam = key

    apps_keys = ["apps", "Apps"]
    for key in apps_keys:
        if key in sharedconfig[configstore][software][valve][steam]:
            apps = key

    apps_list = sharedconfig[configstore][software][valve][steam][apps]

    if fetch_games:
        config_manager = ConfigManager()
        api_key = config_manager.get_steam_api_key()
        steam_id = config_manager.get_steam_id()

        get_owned_games_result = requests.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&include_played_free_games=true&format=json")
        if get_owned_games_result.status_code != 200:
            raise SteamApiError()

        owned_games_json = get_owned_games_result.json()["response"]
        new_games = 0

        for game in owned_games_json["games"]:
            if str(game["appid"]) not in apps_list:
                apps_list[str(game["appid"])] = {}
                apps_list[str(game["appid"])]["tags"] = {}
                apps_list[str(game["appid"])]["tags"]["0"] = "ProtonDB Ranking: 6 Unrated"
                new_games += 1

        print(f"Found {new_games} games from the Steam API.")

    return apps_list

###############################################################################
#             Gets the rating for the game from ProtonDB's API                #
# app_id: (str) The Steam application ID to check ProtonDB for                #
# return: (str) The rating returned from ProtonDB                             #
###############################################################################
def get_protondb_rating(app_id):
    cache_manager = CacheManager()
    (found_in_cache, value) = cache_manager.get_from_protondb_cache(app_id)
    if found_in_cache:
        return value

    protondb_api_result = requests.get(f"https://www.protondb.com/api/v1/reports/summaries/{app_id}.json")
    if protondb_api_result.status_code != 200:
        raise ProtonDBError()
    protondb_api_json = protondb_api_result.json()

    # use trendingTier as this reflects a more up-to-date rating rather than an all-time rating
    protondb_ranking = protondb_api_json["trendingTier"]
    cache_manager.add_to_protondb_cache(app_id, protondb_ranking)

    return protondb_ranking


###############################################################################
#       Tries to find where Steam is installed to on the local machine        #
# return: (str) The path to the Steam install location                        #
###############################################################################
def find_sharedconfig():
    possible_paths = ["~/.local/share/Steam/userdata",
                      "~/.steam/steam/userdata",
                      "~/.steam/root/userdata",
                      "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata",
                      "C:\\Program Files (x86)\\Steam\\userdata"]

    base_path = ""

    for path in possible_paths:
        try:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                base_path = expanded_path
                print(f"Steam found at: {expanded_path}")
                break
        except FileNotFoundError:
            continue

    else:
        print("Could not find Steam! Please pass the path to sharedconfig.vdf with the --sharedconfig parameter.")
        sys.exit()

    # Some people may have more than one Steam user on their PC, this checks for that and asks which you would like to use if multiple are found
    possible_ids = []
    for user_id in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, user_id)):
            username = ""
            try:
                with open(os.path.join(base_path, user_id, "config/localconfig.vdf"), encoding="utf-8") as localconfig_vdf:
                    username = vdf.load(localconfig_vdf)["UserLocalConfigStore"]["friends"]["PersonaName"]
            except:
                username = "(Could not load username from Steam)"
            print(f"Found user {len(possible_ids)}: {user_id}   {username}")
            possible_ids.append(user_id)

    user = 0
    if len(possible_ids) == 1:
        print("Only one user found.")
    else:
        user = input("Which user number would you like to open? ")

    return os.path.join(base_path, possible_ids[int(user)], "7/remote/sharedconfig.vdf")


###############################################################################
#      Checks for an existing ProtonDB Rating tag, if it doesn't have one     #
#      it finds the next available tag number to add for the game             #
# app: (vdf) The vdf dict for the current app                                 #
# return: (str) The number (key) to use for the Steam tag                     #
###############################################################################
def get_tag_number(app):
    tag_num = ""

    if "tags" in app and isinstance(app["tags"], dict):
        # Have to create a copy to avoid: "RuntimeError: dictionary changed size during iteration"
        tags = app["tags"].copy()
        for tag in tags:
            # Search to see if a ProtonDB rank is already a tag, if so just overwrite that tag
            if app["tags"][tag].startswith("ProtonDB Ranking:", 0, 17):
                if not tag_num:
                    tag_num = tag
                else:
                    # Delete dupe tags caused by error of previous versions, may remove this check in the future once its no longer an issue
                    del app["tags"][tag]
        if not tag_num:
            # If no ProtonDB tags were found, use the next available number
            tag_num = str(len(app["tags"]))
    # If the tags key wasn't found, that means there are no tags for the game
    else:
        tag_num = "0"
        app["tags"] = {}

    return tag_num


###############################################################################
#                      Main function, does everything                         #
# args: Arguments passed to the script via command line                       #
###############################################################################
def main(args):
    sharedconfig_path = ""
    no_save = args.no_save
    check_native = args.check_native
    fetch_games = args.fetch_games

    if args.sharedconfig_path:
        # With ~ for user home
        if os.path.exists(os.path.expanduser(args.sharedconfig_path)):
            try:
                with open(args.sharedconfig_path, encoding="utf-8") as sharedconfig_vdf:
                    vdf.load(sharedconfig_vdf)
                sharedconfig_path = os.path.expanduser(args.sharedconfig_path)

            except:
                print(f"Invalid sharedconfig path: '{args.sharedconfig_path}'")
                sys.exit()
        else:
            print(f"Shared config path '{args.sharedconfig_path}' does not exist. Using default path.")

    # If sharedconfig_path was not set with a command line argument, have get_sharedconfig_path() find it
    if not sharedconfig_path:
        sharedconfig_path = find_sharedconfig()

    print(f"Selected: {sharedconfig_path}")
    with open(sharedconfig_path, encoding="utf-8") as sharedconfig_vdf:
        sharedconfig = vdf.load(sharedconfig_vdf)

    # This makes the code slightly cleaner
    apps = get_apps_list(sharedconfig, fetch_games)

    app_count = len(apps)
    print(f"Found {app_count} Steam games")

    for count, app_id in enumerate(apps, 1):
        # This has to be here because some Steam AppID's are strings of text, which ProtonDB does not support. Check test01.vdf line 278 for an example.
        try:
            int(app_id)
        except ValueError:
            continue

        if count > 0 and count % 10 == 0:
            print(f"Processed ({count} of {app_count}) games...")

        protondb_rating = ""
        # If the app is native, no need to check ProtonDB
        if check_native and is_native(app_id):
            protondb_rating = "native"
        else:
            # Get the ProtonDB rating for the app, if ProtonDB 404's it means no rating is available for the game and likely native
            try:
                protondb_rating = get_protondb_rating(app_id)
            except ProtonDBError:
                continue

        tag_num = get_tag_number(apps[app_id])

        # The 1,2,etc. force the better ranks to be at the top, as Steam sorts these alphanumerically
        possible_ranks = {
            "native":   "ProtonDB Ranking: 0 Native",
            "platinum": "ProtonDB Ranking: 1 Platinum",
            "gold":     "ProtonDB Ranking: 2 Gold",
            "silver":   "ProtonDB Ranking: 3 Silver",
            "bronze":   "ProtonDB Ranking: 4 Bronze",
            "pending":  "ProtonDB Ranking: 5 Pending",
            "unrated":  "ProtonDB Ranking: 6 Unrated",
            "borked":   "ProtonDB Ranking: 7 Borked",
        }


        new_rank = True
        try:
            old_tag = apps[app_id]["tags"][tag_num]
            old_key = ""

            # Get the old key (protondb ranking)
            for key, value in possible_ranks.items():
                if value == old_tag:
                    old_key = key
                    break

            # No change since last run, we don't need to output or save it
            if old_key == protondb_rating:
                new_rank = False
            else:
                print(f"{app_id} {old_key} => {protondb_rating} ({count} of {app_count})")
        # If it throws a key error it is a new game to rank
        except KeyError:
            print(f"{app_id} {protondb_rating}")

        if new_rank:
            # Try to inject the tag into the vdfDict, if the returned rating from ProtonDB isn't a key above it will error out
            if protondb_rating in possible_ranks:
                apps[app_id]["tags"][tag_num] = possible_ranks[protondb_rating]
            else:
                print(f"Unknown ProtonDB rating: {protondb_rating}\n Please report this on GitHub!")


    # no_save will be True if -n is passed
    if not no_save:
        print("WARNING: This may clear your current tags on Steam!")
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if check.lower() in ("yes", "y"):
            # Output the edited vdfDict back to the original location
            with open(sharedconfig_path, mode='w', encoding="utf-8") as sharedconfig_vdf:
                vdf.dump(sharedconfig, sharedconfig_vdf, pretty=True)

            # Workaround provided by Valve for the new library
            url = "steam://resetcollections"
            if sys.platform == "win32":
                command = "start "
            else:
                command = "steam "
            input("Please launch Steam, then press Enter to continue...")
            os.system(command + url) #Reset Collections

# Run it
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Add Steam games to categories based on ProtonDB rankings")
    PARSER.add_argument("-c", "--check-native", dest="check_native", action="store_true", default=False, help="Check for native Linux support (WILL add 1+ second per game to lookup if not cached)")
    PARSER.add_argument("-n", "--no-save", dest="no_save", action="store_true", default=False, help="Disable the save option at the end to allow for unattended testing")
    PARSER.add_argument("-f", "--fetch-games", dest="fetch_games", action="store_true", default=False, help="Fetch your games list from your Steam account")
    PARSER.add_argument("-s", "--sharedconfig", dest="sharedconfig_path", help="Specify a custom location for sharedconfig.vdf")
    ARGUMENTS = PARSER.parse_args()

    main(ARGUMENTS)
