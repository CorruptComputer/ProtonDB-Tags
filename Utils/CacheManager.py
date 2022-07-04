import json
import os
import random
import time

class CacheManager:
    def _migrateOldCachePaths(self, cache_path):
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

    def _getCachePath(self):
        cache_path = os.path.expandvars("$XDG_CACHE_HOME")
        if not os.path.exists(cache_path):
            cache_path = os.path.expandvars("$HOME/.cache")

        self._migrateOldCachePaths(cache_path)

        cache_path = os.path.join(cache_path, "ProtonDB-Tags")
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)
    
        return cache_path

    def _getValueFromCache(self, cache_file, app_id):
        cache_path = os.path.join(self._getCachePath(), cache_file)
        found_in_cache = False
        value = False

        if os.path.exists(cache_path):
            with open(cache_path) as cache_file:
                cache = json.load(cache_file)

                if app_id in cache and "time_to_check" in cache[app_id] and "value" in cache[app_id]:
                    if cache[app_id]["time_to_check"] > int( time.time() ):
                        value = cache[app_id]["value"]
                        found_in_cache = True

        return (found_in_cache, value)

    def _addValueToCache(self, cache_file, app_id, value):
        cache_path = os.path.join(self._getCachePath(), cache_file)
        cache = {}
        
        if os.path.exists(cache_path):
            with open(cache_path) as cache_file:
                cache = json.load(cache_file)
        else:
            print("Steam native cache not found.")
            print("Cache will be created here: {}".format(cache_path))

        cache[app_id] = {}                                  # 604800 = seconds in 7 days 86400 = seconds in 1 day
        cache[app_id]["time_to_check"] = int( time.time() ) + 604800 + random.randint(86400, 604800)
        cache[app_id]["value"] = value

        with open(cache_path, 'w') as cache_file:
            json.dump(cache, cache_file)
    
    def GetFromSteamNativeCache(self, app_id):
        return self._getValueFromCache("steamNativeCache.json", app_id)
    
    def AddToSteamNativeCache(self, app_id, value):
        self._addValueToCache("steamNativeCache.json", app_id, value)

    def GetFromProtonDBCache(self, app_id):
        return self._getValueFromCache("protonDBCache.json", app_id)
    
    def AddToProtonDBCache(self, app_id, value):
        self._addValueToCache("protonDBCache.json", app_id, value)