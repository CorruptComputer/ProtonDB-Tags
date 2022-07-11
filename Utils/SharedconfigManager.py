'''Sharedconfig Manager'''

import os
import sys
import vdf


class SharedconfigManager:
    '''Sharedconfig Manager'''

    def _find_sharedconfig(self) -> str:
        '''private: Tries to find where Steam is installed on the local machine.'''

        possible_paths = [
            "~/.local/share/Steam/userdata",
            "~/.steam/steam/userdata",
            "~/.steam/root/userdata",
            "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata",
            "C:\\Program Files (x86)\\Steam\\userdata"
        ]

        base_path = ""

        for path in possible_paths:
            try:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    base_path = expanded_path
                    print(f"Steam found at: {expanded_path}")
                    break
            except FileNotFoundError:
                continue

        else:
            print("Could not find Steam! " + \
                "Please pass the path to sharedconfig.vdf with the --sharedconfig parameter.")
            sys.exit()

        # Some people may have more than one Steam user on their PC,
        # this checks for that and asks which you would like to use if multiple are found
        possible_ids = []
        for user_id in os.listdir(base_path):
            if os.path.isdir(os.path.join(base_path, user_id)):
                username = ""

                try:
                    localconfig_path = os.path.join(base_path, user_id, "config/localconfig.vdf")
                    with open(localconfig_path, encoding="utf-8") as localconfig_vdf:
                        localconfig = vdf.load(localconfig_vdf)

                    for key in ["UserLocalConfigStore", "UserRoamingConfigStore"]:
                        if key in localconfig:
                            configstore = key

                    username = localconfig[configstore]["friends"]["PersonaName"]
                except:
                    username = "(Unknown)"

                print(f"Found user {len(possible_ids)}: {user_id}   {username}")
                possible_ids.append(user_id)

        user = 0
        if len(possible_ids) == 1:
            print("Only one user found.")
        else:
            user = input("Which user number would you like to open? ")

        return os.path.join(base_path, possible_ids[int(user)], "7/remote/sharedconfig.vdf")


    def get_sharedconfig(self, sharedconfig_path: str) -> tuple: # [str, str]
        '''Finds and retreives the contents of the sharedconfig file.\n
           Optionally a path can be given to use instead of searching for it.'''

        if sharedconfig_path:
            # With ~ for user home
            if os.path.exists(os.path.expanduser(sharedconfig_path)):
                try:
                    with open(sharedconfig_path, encoding="utf-8") as sharedconfig_vdf:
                        vdf.load(sharedconfig_vdf)
                    sharedconfig_path = os.path.expanduser(sharedconfig_path)

                except:
                    print(f"Invalid sharedconfig path: '{sharedconfig_path}'")
                    sys.exit()
            else:
                print(f"Shared config path '{sharedconfig_path}' does not exist. " + \
                    "Using default path.")

        # If sharedconfig_path was not set with a command line argument, we need to find it
        if not sharedconfig_path:
            sharedconfig_path = self._find_sharedconfig()

        print(f"Selected: {sharedconfig_path}")
        with open(sharedconfig_path, encoding="utf-8") as sharedconfig_vdf:
            return (sharedconfig_path, vdf.load(sharedconfig_vdf))


    def save_sharedconfig(self, sharedconfig_path: str, sharedconfig_contents: str) -> str:
        '''Overwrites the sharedconfig file with the updated version and tells Steam to import it.\n
           Prompts the user before writing the file.'''

        print("\nWARNING: This may clear your current tags on Steam!")
        check = input("Would you like to save sharedconfig.vdf? (y/N)")
        if check.lower() in ("yes", "y"):
            # Output the edited vdfDict back to the original location
            with open(sharedconfig_path, mode='w', encoding="utf-8") as sharedconfig_vdf:
                vdf.dump(sharedconfig_contents, sharedconfig_vdf, pretty=True)

            # Workaround provided by Valve for the new library
            resetcollections_url = "steam://resetcollections"
            navlibrary_url = "steam://nav/library"
            redirect = "1>/dev/null 2>&1 3>&1 4>&1 5>&1 6>&1 &"
            command = None

            # Windows (good to at least provide the option to folks)
            if sys.platform == "win32":
                command = f"start {resetcollections_url}"
            # Steam installed via Flatpak
            elif "com.valvesoftware.Steam" in sharedconfig_path:
                input("\nPlease close Steam, then press enter to continue...")
                print("Re-launching Flatpak version of Steam...")

                os.system(f"flatpak run com.valvesoftware.Steam {navlibrary_url} {redirect}")
                command = f"flatpak run com.valvesoftware.Steam {resetcollections_url} {redirect}"
            # Steam installed via system package manager
            else:
                command = f"steam {resetcollections_url} {redirect}"

            input("\nMake sure Steam is open, then press enter to continue...")

            if not command:
                print(f"Please open this URL in your browser: {resetcollections_url}")
                sys.exit()

            os.system(command)
            print("Please click 'Confirm' in Steam, this will import the tags into your library.")
