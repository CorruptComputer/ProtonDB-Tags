'''Cache Manager'''

import json
import os
import random
import time

class CacheManager:
    '''Cache Manager'''

    # Need to figure out when this will be safe to remove
    # since at some point theres no reason to keep this around anymore
    def _migrate_old_cache_paths(self, cache_path: str) -> None:
        '''private: Pre 1.1.1 we were not properly using the $XDG_CACHE_HOME value,
           this should migrate our old cache to the correct location.'''

        if os.path.exists(os.path.join(cache_path, ".cache/ProtonDB-Tags")):
            print("Old cache path detected, moving cache to new location...")

            old_cache_path = os.path.join(cache_path, ".cache/ProtonDB-Tags")
            new_cache_path = os.path.join(cache_path, "ProtonDB-Tags")
            os.rename(old_cache_path, new_cache_path)

            if len(os.listdir(os.path.join(cache_path, ".cache"))) == 0:
                print(f"Old cache path '{old_cache_path}' is now empty, removing it...")
                os.rmdir(os.path.join(cache_path, ".cache"))


    def _get_cache_path(self) -> str:
        '''private: Determines the path for the local cache folder that ProtonDB-Tags will use.\n
           Respects $XDG_CACHE_HOME setting.'''

        cache_path = os.path.expandvars("$XDG_CACHE_HOME")
        if not os.path.exists(cache_path):
            cache_path = os.path.expandvars("$HOME/.cache")

        self._migrate_old_cache_paths(cache_path)

        cache_path = os.path.join(cache_path, "ProtonDB-Tags")
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)

        return cache_path


    def __init__(self):
        '''Init, loads or creates the cache if not found.'''

        self._base_cache_path = self._get_cache_path()
        self._steam_native_cache_path = os.path.join(self._base_cache_path, "steamNativeCache.json")
        self._protondb_cache_path = os.path.join(self._base_cache_path, "protonDBCache.json")
        self._steam_native_cache = {}
        self._protondb_cache = {}

        if os.path.exists(self._steam_native_cache_path):
            try:
                with open(self._steam_native_cache_path, encoding="utf-8") as cache_json:
                    self._steam_native_cache = json.load(cache_json)
            except json.JSONDecodeError:
                print("Error reading Steam native cache, creating a new one...")
                self._steam_native_cache = {}
        else:
            print("\nSteam native cache not found.")
            print(f"This will be created here: {self._steam_native_cache_path}")

        if os.path.exists(self._protondb_cache_path):
            try:
                with open(self._protondb_cache_path, encoding="utf-8") as cache_json:
                    self._protondb_cache = json.load(cache_json)
            except json.JSONDecodeError:
                print("Error reading ProtonDB cache, creating a new one...")
                self._protondb_cache = {}
        else:
            print("\nProtonDB cache not found.")
            print(f"This will be created here: {self._protondb_cache_path}")


    def get_from_steam_native_cache(self, app_id: str) -> tuple: # [bool, bool]
        '''Gets a value from the Steam native cache.\n
           If the cached value has expired returns as if it did not exist.'''

        found_in_cache = False
        value = False

        if app_id in self._steam_native_cache:
            app_cache = self._steam_native_cache[app_id]
            if "time_to_check" in app_cache and "value" in app_cache:
                if int(app_cache["time_to_check"]) > int(time.time()):
                    value = app_cache["value"]
                    found_in_cache = True

        return (found_in_cache, value)


    def add_to_steam_native_cache(self, app_id: str, value: bool, days:int = 7, offset:int = 7) \
        -> None:
        '''Adds the specified value to the Steam native cache,
           sets expiration to (7 days + random value 0-7 days).'''

        self._steam_native_cache[app_id] = app_cache = {}

        # 86400 = seconds in 1 day
        # 604800 = seconds in 7 days
        app_cache["time_to_check"] = int(time.time()) + (86400 * days) \
            + random.randint(0, (86400 * offset))

        app_cache["value"] = value


    def get_from_protondb_cache(self, app_id: str) -> tuple: # [bool, str]
        '''Gets a value from the ProtonDB cache.\n
           If the cached value has expired returns as if it did not exist.'''

        found_in_cache = False
        value = False

        if app_id in self._protondb_cache:
            app_cache = self._protondb_cache[app_id]
            if "time_to_check" in app_cache and "value" in app_cache:
                if int(app_cache["time_to_check"]) > int(time.time()):
                    value = app_cache["value"]
                    found_in_cache = True

        return (found_in_cache, value)


    def add_to_protondb_cache(self, app_id: str, value: str, days:int = 7, offset:int = 7) -> None:
        '''Adds the specified value to the ProtonDB cache,
           sets expiration to (7 days + random value 0-7 days).'''

        self._protondb_cache[app_id] = app_cache = {}

        # 86400 = seconds in 1 day
        # 604800 = seconds in 7 days
        app_cache["time_to_check"] = int(time.time()) + (86400 * days) \
            + random.randint(0, (86400 * offset))
            
        app_cache["value"] = value


    def save_caches(self):
        '''Writes the currently cached data to the disk.'''

        with open(self._steam_native_cache_path, mode='w', encoding="utf-8") as cache_file:
            json.dump(self._steam_native_cache, cache_file)

        with open(self._protondb_cache_path, mode='w', encoding="utf-8") as cache_file:
            json.dump(self._protondb_cache, cache_file)
