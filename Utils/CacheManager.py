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


    def _get_value_from_cache(self, cache_file: str, app_id: str) -> tuple[bool, any]:
        '''private: Gets a value from the cache.\n
           If the cached value has expired returns as if it did not exist.'''

        cache_path = os.path.join(self._get_cache_path(), cache_file)
        found_in_cache = False
        value = False

        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as cache_json:
                cache = json.load(cache_json)

                if app_id in cache \
                and "time_to_check" in cache[app_id] \
                and "value" in cache[app_id]:
                    if int(cache[app_id]["time_to_check"]) > int(time.time()):
                        value = cache[app_id]["value"]
                        found_in_cache = True

        return (found_in_cache, value)


    def _add_value_to_cache(self, cache_file: str, app_id: str, value: any) -> None:
        '''private: Adds the specified value to the cache,
           sets expiration to (7 days + random value 1-7 days).'''

        cache_path = os.path.join(self._get_cache_path(), cache_file)
        cache = {}

        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as cache_json:
                cache = json.load(cache_json)
        else:
            print("Steam native cache not found.")
            print(f"Cache will be created here: {cache_path}")

        cache[app_id] = {}               # 604800 = seconds in 7 days     86400 = seconds in 1 day
        cache[app_id]["time_to_check"] = int(time.time()) + 604800 + random.randint(86400, 604800)
        cache[app_id]["value"] = value

        with open(cache_path, mode='w', encoding="utf-8") as cache_json:
            json.dump(cache, cache_json)


    def get_from_steam_native_cache(self, app_id: str) -> tuple[bool, bool]:
        '''Gets a value from the cache.\n
           If the cached value has expired returns as if it did not exist.'''

        return self._get_value_from_cache("steamNativeCache.json", app_id)


    def add_to_steam_native_cache(self, app_id: str, value: bool) -> None:
        '''Adds the specified value to the cache,
           sets expiration to (7 days + random value 1-7 days).'''

        self._add_value_to_cache("steamNativeCache.json", app_id, value)


    def get_from_protondb_cache(self, app_id: str) -> tuple[bool, str]:
        '''Gets a value from the cache.\n
           If the cached value has expired returns as if it did not exist.'''

        return self._get_value_from_cache("protonDBCache.json", app_id)


    def add_to_protondb_cache(self, app_id: str, value: str) -> None:
        '''Adds the specified value to the cache,
           sets expiration to (7 days + random value 1-7 days).'''

        self._add_value_to_cache("protonDBCache.json", app_id, value)
