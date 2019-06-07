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