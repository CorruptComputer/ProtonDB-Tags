#!/usr/bin/python3

import json
import urllib.request
from os import path

import vdf

## Change this to match your system
SHARED_CONFIG = "/home/[USER]/.steam/steam/userdata/[STEAMID3]/7/remote/sharedconfig.vdf"

if not path.exists(SHARED_CONFIG):
    print("Please edit the top of this file to include your steam path!")
    exit()

DATA = vdf.load(open(SHARED_CONFIG))
APPS = DATA["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["Apps"]

for appid in APPS:
    try:
        protondb = json.load(urllib.request.urlopen("https://www.protondb.com/api/v1/reports/summaries/" + str(appid) + ".json"))["trendingTier"] # pylint: disable=line-too-long

        print(str(appid) + " " + protondb)

        APPS[str(appid)]["tags"] = vdf.VDFDict()
        APPS[str(appid)]["tags"]["0"] = protondb

    except ValueError:
        continue

    except urllib.error.HTTPError:
        continue

vdf.dump(DATA, open(SHARED_CONFIG, 'w'), pretty=True)
