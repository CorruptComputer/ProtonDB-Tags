#!/usr/bin/env python3

import argparse
import os
import sys
import time
import json
import vdf
import requests


class ProtonDBError(Exception):
    pass


###############################################################################
#    Checks if the game has Native Linux support from the Steam Store API     #
# app_id: (str) The steam application id to check                             #
# return: (boolean) If the game is native                                     #
###############################################################################
def is_native(app_id):

    # Check for $XDG_CACHE_HOME before defaulting to $HOME.
    cache_path = os.path.expandvars("$XDG_CACHE_HOME")
    if not os.path.exists(cache_path):
        cache_path = os.path.expandvars("$HOME/.cache")

    # If the old cache path exists, then we need to move the files from there and remove it.
    # This should only ever happen if $XDG_CACHE_HOME was set and script run pre 1.1.1.
    if os.path.exists(os.path.join(cache_path, ".cache/ProtonDB-Tags")):
        print("Old cache path detected, moving cache to new location...")
        old_cache_path = os.path.join(cache_path, ".cache/ProtonDB-Tags")
        new_cache_path = os.path.join(cache_path, "ProtonDB-Tags")
        os.rename(old_cache_path, new_cache_path)
        if len(os.listdir(os.path.join(cache_path, ".cache"))) == 0:
            print("Old cache path '{}' is now empty, removing it...".format(os.path.join(cache_path, ".cache/ProtonDB-Tags")))
            os.rmdir(os.path.join(cache_path, ".cache"))

    # Check if the path we want exists, if not create it.
    cache_path = os.path.join(cache_path, "ProtonDB-Tags")
    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)

    # Finally add our file to the end of the path.
    cache_path = os.path.join(cache_path, "steamNativeCache.json")
    cache = {}

    if os.path.exists(cache_path):
        with open(cache_path) as cache_file:
            cache = json.load(cache_file)
        if app_id in cache:
            return cache[app_id] in ["True", "true", True]
    else:
        print("Steam native cache not found.")
        print("Cache will be created here: " + cache_path)


    # Thanks to u/FurbyOnSteroid for finding this!
    # https://www.reddit.com/r/linux_gaming/comments/bxqsvs/protondb_to_steam_library_tool/eqal68r/
    api_url = "https://store.steampowered.com/api/appdetails?appids={}&filters=platforms".format(app_id)
    steam_api_result = requests.get(api_url)
    # Wait 1.3 seconds before continuing, as Steam only allows 10 requests per 10 seconds, otherwise you get rate limited for a few minutes.
    time.sleep(1.3)

    if steam_api_result.status_code != 200:
        print("Error pulling info from Steam API for {}. You're probably being rate-limited or the store page no longer exists.".format(app_id))
        return False

    steam_api_json = steam_api_result.json()

    # If steam can't find the game it will be False
    if steam_api_json[app_id]["success"] in ["True", "true", True]:
        if not os.path.exists(cache_path):
            print("Creating Steam native cache...")
        is_native_game = steam_api_json[app_id]["data"]["platforms"]["linux"] in ["True", "true", True]
        cache[app_id] = str(is_native_game)
        with open(cache_path, 'w') as cache_file:
            json.dump(cache, cache_file)

        return is_native_game

    return False


###############################################################################
#   Checks which ConfigStore you have, some are Local and some are Roaming    #
# sharedconfig: (vdf) The vdf dict to check                                   #
# return: (str) The ConfigStore key to use for the vdf                        #
###############################################################################
def get_configstore_for_vdf(sharedconfig):
    possible_keys = ["UserLocalConfigStore", "UserRoamingConfigStore"]
    for key in possible_keys:
        if key in sharedconfig:
            return key

    sys.exit("Could not load sharedconfig.vdf. Please submit an issue on GitHub and attach your sharedconfig.vdf!")


###############################################################################
#               Get the correct apps key for the sharedconfig                 #
# sharedconfig: (vdf) The vdf dict to check                                   #
# configstore: (str) The ConfigStore key to use for the vdf                   #
# return: (str) The correct key for apps in the vdf                           #
###############################################################################
def get_apps_key(sharedconfig, configstore):
    possible_keys = ["apps", "Apps"]
    for key in possible_keys:
        if key in sharedconfig[configstore]["Software"]["Valve"]["Steam"]:
            return key

    sys.exit("Could not find the apps. Try adding everything to a category before running.")


###############################################################################
#             Gets the rating for the game from ProtonDB's API                #
# app_id: (str) The Steam application ID to check ProtonDB for                #
# return: (str) The rating returned from ProtonDB                             #
###############################################################################
def get_protondb_rating(app_id):
    protondb_api_result = requests.get("https://www.protondb.com/api/v1/reports/summaries/{}.json".format(app_id))
    if protondb_api_result.status_code != 200:
        raise ProtonDBError()
    protondb_api_json = protondb_api_result.json()
    # use trendingTier as this reflects a more up-to-date rating rather than an all-time rating
    return protondb_api_json["trendingTier"]


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
                print("Steam found at: {}".format(expanded_path))
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
                with open(os.path.join(base_path, user_id, "config/localconfig.vdf")) as localconfig_vdf:
                    username = vdf.load(localconfig_vdf)["UserLocalConfigStore"]["friends"]["PersonaName"]
            except:
                username = "(Could not load username from Steam)"
            print("Found user {}: {}   {}".format(len(possible_ids), user_id, username))
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
        app["tags"] = vdf.VDFDict()

    return tag_num


###############################################################################
#                      Main function, does everything                         #
# args: Arguments passed to the script via command line                       #
###############################################################################
def main(args):
    sharedconfig_path = ""
    no_save = args.no_save
    check_native = args.check_native

    if args.sharedconfig_path:
        # With ~ for user home
        if os.path.exists(os.path.expanduser(args.sharedconfig_path)):
            try:
                with open(args.sharedconfig_path) as sharedconfig_vdf:
                    vdf.load(sharedconfig_vdf)
                sharedconfig_path = os.path.expanduser(args.sharedconfig_path)

            except:
                print("Invalid sharedconfig path: '{}'".format(args.sharedconfig_path))
                sys.exit()
        else:
            print("Shared config path '{}' does not exist. Using default path.".format(args.sharedconfig_path))

    # If sharedconfig_path was not set with a command line argument, have get_sharedconfig_path() find it
    if not sharedconfig_path:
        sharedconfig_path = find_sharedconfig()

    print("Selected: {}".format(sharedconfig_path))
    with open(sharedconfig_path) as sharedconfig_vdf:
        sharedconfig = vdf.load(sharedconfig_vdf)

    # Get which version of the configstore you have
    configstore = get_configstore_for_vdf(sharedconfig)

    # This makes the code slightly cleaner
    apps = sharedconfig[configstore]["Software"]["Valve"]["Steam"][get_apps_key(sharedconfig, configstore)]

    appCount = len(apps)
    print("Found {} Steam games".format(appCount))

    for count, app_id in enumerate(apps, 1):
        # This has to be here because some Steam AppID's are strings of text, which ProtonDB does not support. Check test01.vdf line 278 for an example.
        try:
            int(app_id)
        except ValueError:
            continue

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
                print("{} {} => {} ({} of {})".format(app_id, old_key, protondb_rating, count, appCount))
        # If it throws a key error it is a new game to rank
        except KeyError:
            print("{} {}".format(app_id, protondb_rating))

        if new_rank:
            # Try to inject the tag into the vdfDict, if the returned rating from ProtonDB isn't a key above it will error out
            if protondb_rating in possible_ranks:
                apps[app_id]["tags"][tag_num] = possible_ranks[protondb_rating]
            else:
                print("Unknown ProtonDB rating: {}\n Please report this on GitHub!".format(protondb_rating))


    # no_save will be True if -n is passed
    if not no_save:
        print("WARNING: This may clear your current tags on Steam!")
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if check.lower() in ("yes", "y"):
            # Output the edited vdfDict back to the original location
            with open(sharedconfig_path, 'w') as sharedconfig_vdf:
                vdf.dump(sharedconfig, sharedconfig_vdf, pretty=True)

            # Workaround provided by Valve for the new library
            url = "steam://resetcollections"
            if sys.platform == "win32":
                command = "start "
            else:
                command = "xdg-open "
            input("Please launch Steam, then press Enter to continue...")
            os.system(command + url) #Reset Collections

# Run it
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Add Steam games to categories based on ProtonDB rankings")
    PARSER.add_argument("-c", "--check-native", dest="check_native", action="store_true", default=False, help="Check for native Linux support (WILL add 1+ second per game to lookup if not cached)")
    PARSER.add_argument("-n", "--no-save", dest="no_save", action="store_true", default=False, help="Disable the save option at the end to allow for unattended testing")
    PARSER.add_argument("-s", "--sharedconfig", dest="sharedconfig_path", help="Specify a custom location for sharedconfig.vdf")
    ARGUMENTS = PARSER.parse_args()

    main(ARGUMENTS)
