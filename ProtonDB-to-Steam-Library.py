#!/usr/bin/python3

import os
import sys
import json
import urllib.request
import getopt
import vdf

def is_native(app_id):
    try:
        # Thanks to u/FurbyOnSteroid for finding this! https://www.reddit.com/r/linux_gaming/comments/bxqsvs/protondb_to_steam_library_tool/eqal68r/
        steam_api_result = json.load(urllib.request.urlopen("https://store.steampowered.com/api/appdetails?appids=" + app_id + "&filters=platforms"))

        if steam_api_result[app_id]["success"] in ["True", "true", True]:
            return (steam_api_result[app_id]["data"]["platforms"]["linux"] in ["True", "true", True])

        return False
    except urllib.error.HTTPError:
        print("Error pulling info from Steam API for " + app_id + " (you're probably being rate-limited)")
        return False


def get_configstore_for_vdf(sharedconfig):
    configstore = "UserLocalConfigStore"

    try:
        sharedconfig[configstore]
    except KeyError:
        configstore = "UserRoamingConfigStore"

        try:
            sharedconfig[configstore]
        except KeyError:
            print("Could not load sharedconfig.vdf. Please submit an issue on GitHub and attach your sharedconfig.vdf!")
            sys.exit()

    return configstore


def get_protondb_rating(app_id):
    protondb_json = json.load(urllib.request.urlopen("https://www.protondb.com/api/v1/reports/summaries/" + str(app_id) + ".json"))
    return protondb_json["trendingTier"]


def get_sharedconfig_path():
    possible_paths = ["~/.local/share/Steam/userdata",
                      "~/.steam/steam/userdata",
                      "~/.steam/root/userdata"]

    base_path = ""

    for path in possible_paths:
        try:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                base_path = expanded_path
                print("Steam found at: " + expanded_path)
                break
        except FileNotFoundError:
            continue

    else:
        print("Could not find Steam! Please pass the path to sharedconfig.vdf with the -s parameter.")
        sys.exit()

    possible_ids = []
    for user_id in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, user_id)):
            print("Found user " + str(len(possible_ids)) + ": " + user_id + "   " \
                + vdf.load(open(os.path.join(base_path, user_id, "config/localconfig.vdf")))["UserLocalConfigStore"]["friends"]["PersonaName"])
            possible_ids.append(user_id)

    user = 0
    if len(possible_ids) == 1:
        print("Only one user found.")
    else:
        user = input("Which user number would you like to open? ")

    return os.path.join(base_path, possible_ids[int(user)], "7/remote/sharedconfig.vdf")


def main(argv):
    usage = "Usage: ProtonDB-to-Steam-Library.py \n" \
          + "        -s <absolute path to sharedconfig.vdf> \n" \
          + "        -n (disables saving)"
    sharedconfig_path = ""
    skip_save = False

    try:
        opts, _ = getopt.getopt(argv, "hs:n")

    except getopt.GetoptError:
        print(usage)
        sys.exit()

    for opt, arg in opts:
        if opt == "-h":
            print(usage)
            sys.exit()

        elif opt in "-s":
            if os.path.exists(arg):
                try:
                    vdf.load(open(arg))
                    sharedconfig_path = arg
                except:
                    print(arg)
                    print("Invalid path!")
                    sys.exit()

            ## With ~ for user home
            elif os.path.exists(os.path.expanduser(arg)):
                try:
                    vdf.load(open(arg))
                    sharedconfig_path = os.path.expanduser(arg)

                except:
                    print(os.path.expanduser(arg))
                    print("Invalid path!")
                    sys.exit()

            else:
                print(arg)
                print("Invalid path!")
                sys.exit()

        elif opt in "-n":
            skip_save = True


    if not sharedconfig_path:
        sharedconfig_path = get_sharedconfig_path()

    print("Selected: " + sharedconfig_path)
    sharedconfig = vdf.load(open(sharedconfig_path))

    configstore = get_configstore_for_vdf(sharedconfig)

    for app_id in sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"]:
        try:
            # This has to be here because some Steam AppID's are strings of text, which ProtonDB does not support. Check test01.vdf line 278 for an example.
            app_id = int(app_id)
            tag_num = ""

            if is_native(str(app_id)):
                print(str(app_id) + " native")
                continue

            try:
                # Have to create a copy to avoid: "RuntimeError: dictionary changed size during iteration"
                tags = sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"].copy()
                for tag in tags:
                    if sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"][tag].startswith("ProtonDB Ranking:", 0, 17):
                        if not tag_num:
                            tag_num = tag
                        else:
                            # Delete dupe tags caused by error of previous versions, may remove this check in the future once its no longer an issue
                            del sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"][tag]
                if not tag_num:
                    # If no ProtonDB tags were found, use the next available number
                    tag_num = str(len(sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"]))
            except KeyError:
                tag_num = "0"
                sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"] = vdf.VDFDict()

            protondb_rating = get_protondb_rating(app_id)
            print(str(app_id) + " " + protondb_rating)

            # The 1,2,etc. force the better ranks to be at the top, as Steam sorts these alphabetically
            possible_ranks = {
                "platinum": "ProtonDB Ranking: 1 Platinum",
                "gold": "ProtonDB Ranking: 2 Gold",
                "silver": "ProtonDB Ranking: 3 Silver",
                "bronze": "ProtonDB Ranking: 4 Bronze",
                "pending": "ProtonDB Ranking: 5 Pending",
                "unrated": "ProtonDB Ranking: 6 Unrated",
                "borked": "ProtonDB Ranking: 7 Borked",
            }

            try:
                sharedconfig[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(app_id)]["tags"][tag_num] = possible_ranks[protondb_rating]
            except KeyError:
                print("Unknown ProtonDB rating: " + protondb_rating + "\n Please report this on GitHub!")

        except urllib.error.HTTPError:
            continue
        except ValueError:
            continue

    if not skip_save:
        print("WARNING: This may clear your current tags on Steam!")
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if check.lower() in ("yes", "y"):
            vdf.dump(sharedconfig, open(sharedconfig_path, 'w'), pretty=True)

if __name__ == "__main__":
    main(sys.argv[1:])
