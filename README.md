# ProtonDB-Tags [![Build Status](https://travis-ci.com/CorruptComputer/ProtonDB-Tags.svg?branch=master)](https://travis-ci.com/CorruptComputer/ProtonDB-Tags)[<img src="https://discordapp.com/assets/f8389ca1a741a115313bede9ac02e2c0.svg" width="45" height="45" alt="Discord" title="Discord">](https://discord.gg/87fJcCY)

**Just a quick heads up, the script has been renamed to ProtonDB-Tags.py!**

This is just a small python script to pull ratings from ProtonDB and import them into your Steam library as tags.

Here is a screenshot which shows how it looks once ran:

![Screenshot](screenshot.png)

### Dependencies

This script requires Python 3, you can check your python version with `python --version`. If your default is Python 2 then you'll need to check with your distro's documentation and install Python 3, then replace all of the below commands with `python3` and `pip3`.

You'll need to install [vdf](https://github.com/ValvePython/vdf) and [requests](https://2.python-requests.org/en/master/) before this can run.
You can install them via pip with:
```bash
pip install requests vdf
```

Alternatively you can use the included requirements.txt file:
```bash
pip install -r requirements.txt
```

### Running

**WARNING:** This may clear all of your current tags in Steam. You have been warned!

This can be simply run with: 
```bash
python ProtonDB-Tags.py
```

It will also ask before saving the file, so if you want to just test it out theres no real danger of overwriting anything.

By default this will not check the Steam API for native titles. This can be enabled with the `--check-native` flag. This will add a 1 second wait to each Steam API call, as without this you will get rate-limited. The script will build a cache of these as it runs, so after the first run it will go faster.

You can also specify a custom path to your sharedconfig.vdf with: 
```bash
python ProtonDB-Tags.py --sharedconfig /path/to/sharedconfig.vdf
```

The full command line options can be viewed with: 
```bash
python ProtonDB-Tags.py --help
```

### Contributing

If you run into any issues please attach the output from the script to your issue, along with the sharedconfig.vdf file which was selected.

All feedback is welcome and appreciated! Please make an issue if you have any ideas or feedback, I would love to hear them!

If you would like to make a PR all I ask is that you are also open to feedback on your written code.

### Troubleshooting

If you are finding that only some of your Proton compatible games are being categorized try this:
1. Select all of the uncategorized games in your library
2. Right click -> Add to -> ProtonDB Ranking: 7 Borked
3. File -> Exit Steam to force it to write all of your games to the sharedconfig.vdf file
4. Try running the script again

Please keep in mind that most Linux Native games will not be categorized without the `--check-native` flag, as ProtonDB doesn't return anything for them.

If you get an error which looks like this:
```
WARNING: This may clear your current tags on Steam!
Would you like to save sharedconfig.vdf? (y/N)y
Traceback (most recent call last):
  File "ProtonDB-Tags.py", line 220, in 
    main(arguments)
  File "ProtonDB-Tags.py", line 207, in main
    check = input("Would you like to save sharedconfig.vdf? (y/N)")
  File "", line 1, in 
    NameError: name 'y' is not defined
```
It means you ran the script with python2, please run it with python3. More info about why this error happens can be found [here](https://stackoverflow.com/a/21122817).

If anything is still not working you can open an issue here, or join my Discord server (link is at the top of this README). Please respect the rules of the server if you join!
