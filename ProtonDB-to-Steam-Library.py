#!/usr/bin/python3

import argparse
import os
import sys
import time
import vdf

import requests

class ProtonDBError(Exception):
    pass

# Python 2 compatability
try:
    input = raw_input
except NameError:
    pass

# Checks if the game has Native Linux support
# In the near futute I would like to add caching to this in order to speed up the runtime of the script.
# However, it needs to be implemented in a way so that it re-checks after a set amount of time to see if anything has changed.
def is_native(app_id):
    # Wait 1 second before continuing, as Steam only allows 10 requests per 10 seconds, otherwise you get rate limited for a few minutes.
    time.sleep(1)

    # Thanks to u/FurbyOnSteroid for finding this! https://www.reddit.com/r/linux_gaming/comments/bxqsvs/protondb_to_steam_library_tool/eqal68r/
    steam_api_result = requests.get("https://store.steampowered.com/api/appdetails?appids={}&filters=platforms".format(app_id))
    if steam_api_result.status_code != 200:
        print("Error pulling info from Steam API for {}. You're probably being rate-limited".format(app_id))
        return False

    steam_api_json = steam_api_result.json()

    # If steam can't find the game it will be False
    if steam_api_json[app_id]["success"] in ["True", "true", True]:
        return (steam_api_json[app_id]["data"]["platforms"]["linux"] in ["True", "true", True])

    return False

# Checks which version of the sharedconfig you have, some are Local and some are Remote
def get_configstore_for_vdf(sharedconfig):
    possibleKeys = ["UserLocalConfigStore", "UserRoamingConfigStore"]
    for key in possibleKeys:
        if key in sharedconfig:
            return key

    sys.exit("Could not load sharedconfig.vdf. Please submit an issue on GitHub and attach your sharedconfig.vdf!")

# Get the correct apps key.
def get_apps_key(sharedconfig, configstore):
    possibleKeys = ["apps", "Apps"]
    for key in possibleKeys:
        if key in sharedconfig[configstore]["Software"]["Valve"]["Steam"]:
            return key

    sys.exit("Could not find the apps. Try adding everything to a category before running.")


# Pulls the games ranking from ProtonDB and returns the Teir as a string
def get_protondb_rating(app_id):
    protondb_api_result = requests.get("https://www.protondb.com/api/v1/reports/summaries/{}.json".format(app_id))
    if protondb_api_result.status_code != 200:
        raise ProtonDBError()
    protondb_api_json = protondb_api_result.json()
    # use trendingTier as this reflects a more up-to-date rating rather than an all-time rating
    return protondb_api_json["trendingTier"]

# Trys to find the path to your localconfig.vdf, these are the most common Steam install locations
def get_sharedconfig_path():
    possible_paths = ["~/.local/share/Steam/userdata",
                      "~/.steam/steam/userdata",
                      "~/.steam/root/userdata",
                      "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata"]

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
        print("Could not find Steam! Please pass the path to sharedconfig.vdf with the -s parameter.")
        sys.exit()

    # Some people may have more than one Steam user on their PC, this checks for that and asks which you would like to use if multiple are found
    possible_ids = []
    for user_id in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, user_id)):
            username = ""
            try:
                username = vdf.load(open(os.path.join(base_path, user_id, "config/localconfig.vdf")))["UserLocalConfigStore"]["friends"]["PersonaName"]
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

def get_tag_number(app):
    tag_num = ""

    if "tags" in app \
    and isinstance(app["tags"], dict):
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


def main(args):
    sharedconfig_path = ""
    no_save = args.no_save
    check_native = args.check_native

    if args.sharedconfig_path:
        # With ~ for user home
        if os.path.exists(os.path.expanduser(args.sharedconfig_path)):
            try:
                vdf.load(open(args.sharedconfig_path))
                sharedconfig_path = os.path.expanduser(args.sharedconfig_path)

            except:
                print("Invalid sharedconfig path: '{}'".format(args.sharedconfig_path))
                sys.exit()
        else:
            print("Shared config path '{}' does not exist. Using default path.".format(args.sharedconfig_path))

    # If sharedconfig_path was not set with a command line arguement, have get_sharedconfig_path() find it
    if not sharedconfig_path:
        sharedconfig_path = get_sharedconfig_path()

    print("Selected: {}".format(sharedconfig_path))
    sharedconfig = vdf.load(open(sharedconfig_path))

    # Get which version of the configstore you have
    configstore = get_configstore_for_vdf(sharedconfig)

    # This makes the code slightly cleaner
    apps = sharedconfig[configstore]["Software"]["Valve"]["Steam"][get_apps_key(sharedconfig, configstore)]

    for app_id in apps:
        # This has to be here because some Steam AppID's are strings of text, which ProtonDB does not support. Check test01.vdf line 278 for an example.
        try:
            int(app_id)
        except ValueError:
            continue

        protondb_rating = ""
        # If the app is native, no need to check ProtonDB
        if check_native and is_native(app_id):
            protondb_rating = "native"
            print("{} native".format(app_id))
        else:
            # Get the ProtonDB rating for the app, if ProtonDB 404's it means no rating is available for the game and likely native
            try:
                protondb_rating = get_protondb_rating(app_id)
                print("{} {}".format(app_id, protondb_rating))
            except ProtonDBError:
                continue

        tag_num = get_tag_number(apps[app_id])

        # The 1,2,etc. force the better ranks to be at the top, as Steam sorts these alphabetically
        possible_ranks = {
            "native": "ProtonDB Ranking: 0 Native", # This should probably be changed eventually, but this is to allow us to scan the tags for an existing one.
            "platinum": "ProtonDB Ranking: 1 Platinum",
            "gold": "ProtonDB Ranking: 2 Gold",
            "silver": "ProtonDB Ranking: 3 Silver",
            "bronze": "ProtonDB Ranking: 4 Bronze",
            "pending": "ProtonDB Ranking: 5 Pending",
            "unrated": "ProtonDB Ranking: 6 Unrated",
            "borked": "ProtonDB Ranking: 7 Borked",
        }

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
            # Output the edited vdfDict back to the origional location
            vdf.dump(sharedconfig, open(sharedconfig_path, 'w'), pretty=True)

# Run it
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add Steam games to categories based on ProtonDB rankings")
    parser.add_argument("-c", "--check-native", dest="check_native", action="store_true", default=False, help="Check Steam API for native Linux support (WILL add 1+ second per game to lookup)")
    parser.add_argument("-n", "--no-save", dest="no_save", action="store_true", default=False, help="Disable the save option at the end to allow for unattended testing")
    parser.add_argument("-s", "--sharedconfig", dest="sharedconfig_path", help="Specify a custom location for sharedconfig.vdf")
    arguments = parser.parse_args()

    main(arguments)
