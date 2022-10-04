#!/usr/bin/env python3
'''ProtonDB Tags'''

import argparse
import time
import requests

from Utils.CacheManager import CacheManager
from Utils.ConfigManager import ConfigManager
from Utils.SharedconfigManager import SharedconfigManager


class ProtonDBError(Exception):
    '''If ProtonDB returns an error or rate limits us, we will throw this exception.'''


def is_native(app_id: str, skip_cache: bool, cache_manager: CacheManager) -> bool:
    '''Checks if the game has Native Linux support from the Steam Store API.'''

    if not skip_cache:
        (found_in_cache, value) = cache_manager.get_from_steam_native_cache(app_id)
        if found_in_cache:
            return value

    # Thanks to u/FurbyOnSteroid for finding this!
    # https://www.reddit.com/r/linux_gaming/comments/bxqsvs/protondb_to_steam_library_tool/eqal68r/
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=platforms"
    steam_response = None
    is_native_game = False

    try:
        steam_response = requests.get(api_url, timeout=3)
    except requests.Timeout:
        print(f"{app_id} | Timed out reading Steam store page.")
    except requests.ConnectionError:
        print(f"{app_id} | Could not connect to ProtonDB")
    except requests.RequestException:
        print(f"{app_id} | An unknown error occoured when the request to ProtonDB")

    # Wait 1.3 seconds before continuing, as Steam only allows 10 requests per 10 seconds,
    # otherwise you get rate limited for a few minutes.
    time.sleep(1.3)

    if steam_response:
        if steam_response.status_code != 200:
            print(f"{app_id} | Error reading Steam store info for game.")
            return False

        steam_api_json = steam_response.json()

        # If steam can't find the game it will be False
        is_success = steam_api_json[app_id]["success"]
        is_native_game = False

        if is_success in ["True", "true", True]:
            linux_support = steam_api_json[app_id]["data"]["platforms"]["linux"]
            is_native_game = linux_support in ["True", "true", True]

        cache_manager.add_to_steam_native_cache(app_id, is_native_game)
    else:
        # give a 1 day cooldown to reduce server load and speed when retrying after a long run
        cache_manager.add_to_steam_native_cache(app_id, is_native_game, 1, 0)

    return is_native_game


def get_key_value(possible_keys, dict_to_check: dict) -> str:
    '''Finds which key exists in the dict.\n
       If none of the values are found the first will be taken as a default.\n
       possible_keys should be of type str[]'''

    found_key = "Not found"
    for key in possible_keys:
        if key in dict_to_check:
            found_key = key

    if found_key == "Not found":
        found_key = possible_keys[0]
        dict_to_check[found_key] = {}

    return found_key


def get_apps_list(sharedconfig: dict, fetch_games: bool) -> dict:
    '''Searches the sharedconfig to get a list of Steam app IDs.\n
       Optionally can query the Steam API to check for games as well.'''

    # If neither value is found, the first will be taken as a default and initialized to {}
    configstore = get_key_value(["UserRoamingConfigStore", "UserLocalConfigStore"], sharedconfig)
    software = get_key_value(["Software", "software"], sharedconfig[configstore])
    valve = get_key_value(["Valve", "valve"], sharedconfig[configstore][software])
    steam = get_key_value(["Steam", "steam"], sharedconfig[configstore][software][valve])
    apps = get_key_value(["Apps", "apps"], sharedconfig[configstore][software][valve][steam])

    apps_list = sharedconfig[configstore][software][valve][steam][apps]

    if fetch_games:
        config_manager = ConfigManager()
        api_key = config_manager.get_steam_api_key()
        steam_id = config_manager.get_steam_id()

        api_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/" + \
            f"?key={api_key}" + \
            f"&steamid={steam_id}" + \
            "&include_played_free_games=true" + \
            "&skip_unvetted_apps=false" + \
            "&include_free_sub=true" + \
            "&format=json"

        get_owned_games_result = requests.get(api_url, timeout=3)
        if get_owned_games_result.status_code != 200:
            print("There was a problem retreiving your games list from the Steam API, " + \
                f"status code was: {get_owned_games_result.status_code}")

            if get_owned_games_result.status_code == 401:
                print("A 401 status code usually means authentication failure, " + \
                    "your API key is most likely invalid.")
            elif get_owned_games_result.status_code == 500:
                print("A 500 status code usually means server error, " + \
                    "your steamID64 may be invalid or Steam is currently down.")

            config_manager.clear_config()
            return apps_list

        owned_games_json = get_owned_games_result.json()["response"]
        new_games = 0

        if "games" not in owned_games_json:
            print("\nNo games returned by the Steam API for your account. " + \
                "This usually means that your profile and games list are set to private.")

            print("If you are uncomfortable having a public profile, don't worry. " + \
                "This only needs to be public for long enough to run the script.")

            print("\nThese settings can be changed here: " + \
                "https://steamcommunity.com/my/edit/settings")

            return apps_list


        for game in owned_games_json["games"]:
            if str(game["appid"]) not in apps_list:
                apps_list[str(game["appid"])] = {}
                apps_list[str(game["appid"])]["tags"] = {}
                new_games += 1

        print(f"Found {new_games} new games from the Steam API.")

    return apps_list


def get_protondb_rating(app_id: str, skip_cache: bool, cache_manager: CacheManager) -> str:
    '''Gets the rating for the game from ProtonDB's API.
       Defaults to 'unrated' if there is a problem with the ProtonDB API.'''

    if not skip_cache:
        (found_in_cache, value) = cache_manager.get_from_protondb_cache(app_id)
        if found_in_cache:
            return value

    # For example, Warframe: https://www.protondb.com/api/v1/reports/summaries/230410.json
    api_url = f"https://www.protondb.com/api/v1/reports/summaries/{app_id}.json"
    protondb_response = None
    protondb_ranking = "unrated"

    try:
        protondb_response = requests.get(api_url, timeout=3)
    except requests.Timeout:
        print(f"{app_id} | Timed out reading the ranking from ProtonDB")
    except requests.ConnectionError:
        print(f"{app_id} | Could not connect to ProtonDB")
    except requests.RequestException:
        print(f"{app_id} | An unknown error occoured when the request to ProtonDB")

    if protondb_response:
        if protondb_response.status_code == 200:
            protondb_data = protondb_response.json()
            protondb_ranking = protondb_data["trendingTier"]

        cache_manager.add_to_protondb_cache(app_id, protondb_ranking)
    else:
        # give a 1 day cooldown to reduce server load and speed when retrying after a long run
        cache_manager.add_to_protondb_cache(app_id, protondb_ranking, 1, 0)

    return protondb_ranking


def get_tag_number(app: dict) -> str:
    '''Checks for an existing ProtonDB Rating tag,
       if it doesn't have one it finds the next available tag number to add for the game.'''

    tag_num = None

    if "tags" in app and isinstance(app["tags"], dict):
        # Have to create a copy to avoid: "RuntimeError: dictionary changed size during iteration"
        tags = app["tags"].copy()
        for tag in tags:
            # Search to see if a ProtonDB rank is already a tag, if so just overwrite that tag
            if app["tags"][tag].startswith("ProtonDB Ranking:", 0, 17):
                if not tag_num:
                    tag_num = tag
                else:
                    # Delete dupe tags caused by error of previous versions,
                    # may remove this check in the future once its no longer an issue
                    del app["tags"][tag]
        if not tag_num:
            # If no ProtonDB tags were found, use the next available number
            tag_num = str(len(app["tags"]))

    # If the tags key wasn't found, that means there are no tags for the game
    else:
        tag_num = "0"
        app["tags"] = {}

    return tag_num


def main(args) -> None:
    '''Main entry point into the script.'''

    if args.clear_config:
        config_manager = ConfigManager()
        config_manager.clear_config()

    sharedconfig_manager = SharedconfigManager()
    (sharedconfig_path, sharedconfig) = \
        sharedconfig_manager.get_sharedconfig(args.sharedconfig_path)

    # This makes the code slightly cleaner
    apps = get_apps_list(sharedconfig, args.fetch_games)

    cache_manager = CacheManager()
    app_count = len(apps)

    print(f"\nFound a total of {app_count} Steam games.")
    start_time = time.time()

    for count, app_id in enumerate(apps, 1):
        # This has to be here because some Steam AppID's are strings of text,
        # which ProtonDB does not support. Check test01.vdf line 278 for an example.
        try:
            int(app_id)
        except ValueError:
            continue

        game_rating = ""
        # If the app is native, no need to check ProtonDB
        if args.check_native and is_native(app_id, args.skip_cache, cache_manager):
            game_rating = "native"
        else:
            # Get the ProtonDB rating for the app, if nothing returned defaults to unrated
            game_rating = get_protondb_rating(app_id, args.skip_cache, cache_manager)

        tag_num = get_tag_number(apps[app_id])

        # The numbers force the better ranks to be at the top, as Steam sorts these alphanumerically
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

        if "tags" not in apps[app_id]:
            apps[app_id]["tags"] = {}

        if tag_num in apps[app_id]["tags"]:
            old_tag = apps[app_id]["tags"][tag_num]
            old_key = ""

            # Get the old key (protondb ranking)
            for key, value in possible_ranks.items():
                if value == old_tag:
                    old_key = key
                    break

            # No change since last run, we don't need to output or save it
            if old_key == game_rating:
                new_rank = False
            else:
                print(f"{app_id} | {old_key} => {game_rating} ({count} of {app_count})")
        else:
            print(f"{app_id} | {game_rating} ({count} of {app_count})")

        if new_rank:
            # Try to inject the tag into the vdfDict, if the returned rating from ProtonDB isn't a
            # key in possible_ranks it will error out
            if game_rating in possible_ranks:
                apps[app_id]["tags"][tag_num] = possible_ranks[game_rating]
            else:
                print(f"Unknown ProtonDB rating: {game_rating}\n Please report this on GitHub!")

        if count > 0 and count % 10 == 0:
            print(f"Processed ({count} of {app_count}) games...")
            cache_manager.save_caches() # Save every once in awhile

    cache_manager.save_caches()
    end_time = time.time() - start_time

    print(f"Took a total of {round(end_time, 2)} seconds to process, " + \
        f"with an average of {round(end_time / app_count, 2)} seconds per game")

    # True if -n or --no-save is passed
    if not args.no_save:
        sharedconfig_manager.save_sharedconfig(sharedconfig_path, sharedconfig)

# Run it
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description = "Add Steam games to categories based on ProtonDB rankings"
    )

    PARSER.add_argument(
        "-c", "--check-native",
        dest = "check_native",
        action = "store_true",
        default = False,
        help = "Check for native Linux support (will add 1.3 seconds per non-cached game)"
    )

    PARSER.add_argument(
        "-n", "--no-save",
        dest = "no_save",
        action = "store_true",
        default = False,
        help = "Disable the save option at the end to allow for unattended testing"
    )

    PARSER.add_argument(
        "-f", "--fetch-games",
        dest = "fetch_games",
        action = "store_true",
        default = False,
        help = "Fetch your games list from the Steam API"
    )

    PARSER.add_argument(
        "--clear-config",
        dest = "clear_config",
        action = "store_true",
        default = False,
        help = "Clear your current config, useful if the values in there need to be refreshed."
    )

    PARSER.add_argument(
        "--skip-cache",
        dest = "skip_cache",
        action = "store_true",
        default = False,
        help = "Skip reading your current cache, values retreived will still be added to the cache."
    )

    PARSER.add_argument(
        "-s", "--sharedconfig",
        dest = "sharedconfig_path",
        default = None,
        help = "Specify a custom location for sharedconfig.vdf"
    )

    ARGUMENTS = PARSER.parse_args()

    main(ARGUMENTS)
