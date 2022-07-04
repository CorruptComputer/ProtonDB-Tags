
import json
import os


class ConfigManager:
    def _getConfigPath(self):
        config_path = os.path.expandvars("$XDG_CONFIG_HOME")
        if not os.path.exists(config_path):
            config_path = os.path.expandvars("$HOME/.config")

        config_path = os.path.join(config_path, "ProtonDB-Tags")
        if not os.path.isdir(config_path):
            os.makedirs(config_path)
    
        return config_path

    def GetSteamId(self):
        config_path = os.path.join(self._getConfigPath(), "config.json")
        config = {}

        if os.path.exists(config_path):
            with open(config_path) as config_file:
                config = json.load(config_file)
            if "steam_id" in config:
                return config["steam_id"]
        else:
            print("Existing config not found.")
            print("Config will be created here: {}".format(config_path))

        print("Please go here to find your steamID64: https://steamid.io")

        steam_id = input("steamID64: ")

        #TODO: validate the steamID64 is valid

        config["steam_id"] = steam_id

        with open(config_path, 'w') as config_file:
                json.dump(config, config_file)
        
        return steam_id
    
    def GetSteamApiKey(self):
        config_path = os.path.join(self._getConfigPath(), "config.json")
        config = {}

        if os.path.exists(config_path):
            with open(config_path) as config_file:
                config = json.load(config_file)
            if "steam_api_key" in config:
                return config["steam_api_key"]
        else:
            print("Existing config not found.")
            print("Config will be created here: {}".format(config_path))

        print("Due to recent changes in Steam, it has become more difficult to get an accurate list the games in your library.")
        print("In order to work around this, we can use the Steam API to get this information directly.")
        print("Please go here to generate an API key: https://steamcommunity.com/dev/apikey")
        print("\nThis API key will be saved in the config for ProtonDB-Tags on your PC.")

        api_key = input("Api key: ")

        #TODO: validate the API key works

        config["steam_api_key"] = api_key

        with open(config_path, 'w') as config_file:
                json.dump(config, config_file)
        
        return api_key