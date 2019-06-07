# ProtonDB to Steam Library

This is just a small python script I made to pull ratings from ProtonDB and import them into your Steam library as tags. 

### Running

**WARNING:** This will clear all of your current tags in Steam. You have been warned!

You'll need to edit the file and add your Steam install path and UserID to here:

```python
sharedconfig = "/home/[user]/.steam/steam/userdata/[userID]/7/remote/sharedconfig.vdf"
```

Once that is set you'll want to close Steam and run with: `python ProtonDB-to-Steam-Library.py`

### Made with:

https://github.com/ValvePython/vdf