#!/usr/bin/python3

import os, sys, json, urllib.request, vdf, getopt

def main(argv):
    sharedconfig = ""
    save = None

    try:
        opts, args = getopt.getopt(argv, "hs:n")
    except getopt.GetoptError:
        print("ProtonDB-to-Steam-Library.py [-s <absolute path to sharedconfig.vdf>] [-n (disable saving)]")
        exit()
    for opt, arg in opts:
        if opt == '-h':
            print("ProtonDB-to-Steam-Library.py [-s <absolute path to sharedconfig.vdf>] [-n (disable saving)]")
            exit()
        elif opt in ("-s"):
            if (os.path.exists(arg)):
                try:
                    vdf.load(open(arg))
                    sharedconfig = arg
                except:
                    print(arg)
                    print("Invalid path! 1")
                    exit()
            ## With ~ for user home
            elif (os.path.exists(os.path.expanduser(arg))):
                try:
                    vdf.load(open(arg))
                    sharedconfig = os.path.expanduser(arg)
                except:
                    print(os.path.expanduser(arg))
                    print("Invalid path! 2")
                    exit()
            else:
                print(arg)
                print("Invalid path! 4")
                exit()
        elif opt in ("-n"):
            save = False

    if (sharedconfig == ""):
        path1 = os.path.expanduser('~/.local/share/Steam/userdata')
        path2 = os.path.expanduser('~/.steam/steam/userdata')
        # Not sure if I really would like to support this one long term as running Steam as root seems strange
        path3 = os.path.expanduser('~/.steam/root/userdata')

        basepath = ""
        if (os.path.exists(path1)):
            print("Steam found at: " + path1)
            basepath = path1
        elif (os.path.exists(path2)):
            print("Steam found at: " + path2)
            basepath = path2
        elif (os.path.exists(path3)):
            print("Steam found at: " + path3)
            basepath = path3
        else:
            print("Could not find Steam! Please pass the path to sharedconfig.vdf with the -s parameter.")
            exit()

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

    print("Selectd: " + sharedconfig)        
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
            exit()

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

    if (save == None):
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if (check.lower() == "y" or check.lower() == "yes"):
            save = True
        else:
            save = False

    if (save):
        vdf.dump(data, open(sharedconfig, 'w'), pretty=True)


main(sys.argv[1:])