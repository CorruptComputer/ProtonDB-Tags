#!/usr/bin/python3

import os, sys, json, urllib.request, vdf, getopt

def main(argv):
    sharedconfig = ""
    skipsave = False

    try:
        opts, _ = getopt.getopt(argv, "hs:n")

    except getopt.GetoptError:
        print("ProtonDB-to-Steam-Library.py [-s <absolute path to sharedconfig.vdf>] [-n (disable saving)]")
        sys.exit()

    for opt, arg in opts:
        if opt == '-h':
            print("ProtonDB-to-Steam-Library.py [-s <absolute path to sharedconfig.vdf>] [-n (disable saving)]")
            sys.exit()

        elif opt in ("-s"):
            if (os.path.exists(arg)):
                try:
                    vdf.load(open(arg))
                    sharedconfig = arg
                except:
                    print(arg)
                    print("Invalid path! 1")
                    sys.exit()

            ## With ~ for user home
            elif (os.path.exists(os.path.expanduser(arg))):
                try:
                    vdf.load(open(arg))
                    sharedconfig = os.path.expanduser(arg)

                except:
                    print(os.path.expanduser(arg))
                    print("Invalid path! 2")
                    sys.exit()

            else:
                print(arg)
                print("Invalid path! 4")
                sys.exit()

        elif opt in ("-n"):
            skipsave = True


    if (not sharedconfig):
        paths = ['~/.local/share/Steam/userdata',
                 '~/.steam/steam/userdata',
                 # Not sure if I really would like to support this one long term as running Steam as root seems strange
                 '~/.steam/root/userdata']

        basepath = ""

        for path in paths:
            try:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    basepath = expanded_path
                    print("Steam found at: " + expanded_path)
                    break
            except FileNotFoundError:
                continue

        else:
            print("Could not find Steam! Please pass the path to sharedconfig.vdf with the -s parameter.")
            sys.exit()

        possibleIDs = []
        for userID in os.listdir(basepath):
            if os.path.isdir(os.path.join(basepath, userID)):
                print("Found user " + str(len(possibleIDs)) + ": " + userID + "   " \
                    + vdf.load(open(os.path.join(basepath, userID, "config/localconfig.vdf")))["UserLocalConfigStore"]["friends"]["PersonaName"])
                possibleIDs.append(userID)

        user = 0
        if (len(possibleIDs) == 1):
            print("Only one user found.")
            user = 0
        else:
            user = input("Which user number would you like to open? ")
        sharedconfig = os.path.join(basepath, possibleIDs[int(user)], "7/remote/sharedconfig.vdf") 

    print("Selected: " + sharedconfig)        
    data = vdf.load(open(sharedconfig))

    configstore = "UserLocalConfigStore"

    try:
        data[configstore]

    except KeyError:
        configstore = "UserRoamingConfigStore"
        try:
            data[configstore]
        except KeyError:
            print("Could not load sharedconfig.vdf. Please submit an issue on GitHub and attach your sharedconfig.vdf!")
            sys.exit()


    for appid in data[configstore]["Software"]["Valve"]["Steam"]["Apps"]:
        try:
            appid = int(appid)
            protondb = json.load(urllib.request.urlopen("https://www.protondb.com/api/v1/reports/summaries/" + str(appid) + ".json"))["trendingTier"]

            print(str(appid) + " " + protondb)

            data[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(appid)]["tags"] = vdf.VDFDict()
            data[configstore]["Software"]["Valve"]["Steam"]["Apps"][str(appid)]["tags"]["0"] = "ProtonDB Ranking: " + protondb
            
        except ValueError:
            continue
        
        except urllib.error.HTTPError:
            continue

    if (not skipsave):
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if (check.lower() in ("yes","y")):
            vdf.dump(data, open(sharedconfig, 'w'), pretty=True)

if __name__ == "__main__":
    main(sys.argv[1:])