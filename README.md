# ProtonDB to Steam Library [![Build Status](https://travis-ci.com/CorruptComputer/ProtonDB-to-Steam-Library.svg?branch=master)](https://travis-ci.com/CorruptComputer/ProtonDB-to-Steam-Library)

This is just a small python script I made to pull ratings from ProtonDB and import them into your Steam library as tags.

Here is a screenshot which shows how it looks once ran:

![Screenshot](screenshot.png)

### Dependencies

You'll need to install [vdf](https://github.com/ValvePython/vdf) before this can run. 
You can install it via pip with `pip install vdf`

### Running

**WARNING:** This will clear all of your current tags in Steam. You have been warned!

This can be simply run with: `python ProtonDB-to-Steam-Library.py`

You can also specify a custom path to your `sharedconfig.vdf` with: `python ProtonDB-to-Steam-Library.py -s /path/to/sharedconfig.vdf`

If you'd like to just run this as a test, with no saving of the vdf file, you can just specify the -n parameter: `python ProtonDB-to-Steam-Library.py -n`

### Troubleshooting

If you are finding that only some of your Proton compatible games are being categorized try this:

1. Select all of the games in your library
2. Right click -> Set Categories...
3. Add some random category to them all (will be removed)
4. Close Steam to force it to write all of your games to the sharedconfig.vdf file
5. Try running the script again

Please keep in mind that Native games shouldn't be categorized, except in some rare cases such as Deus Ex: Mankind Divided. This means people have reported it on ProtonDB for some reason so the ProtonDB API returns a result for it.
