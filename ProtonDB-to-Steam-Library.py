#!/usr/bin/python3

import os.path
from os import path
import vdf
import urllib.request
import json

## Change this to match your system
sharedconfig = "/home/[user]/.steam/steam/userdata/[UserID]/7/remote/sharedconfig.vdf"

if (path.exists(sharedconfig) != True):
    print("Please edit the top of this file to include your steam path!")
    exit()

data = vdf.load(open(sharedconfig))

for appid in data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["Apps"]:
    try:
        appid = int(appid)
        protondb = json.load(urllib.request.urlopen("https://www.protondb.com/api/v1/reports/summaries/" + str(appid) + ".json"))["trendingTier"]

        print(str(appid) + " " + protondb)

        data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["Apps"][str(appid)]["tags"] = vdf.VDFDict()
        data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["Apps"][str(appid)]["tags"]["0"] = protondb
        
    except ValueError:
        continue
    
    except urllib.error.HTTPError:
        continue

vdf.dump(data, open(sharedconfig,'w'), pretty=True)
