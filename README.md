# GTFO_MapGeneration

This project is used to generate maps either before a run or to see where item spawns are.

This is in theory the true successor of WardenMapper. Kind of.

## What can it do:

1. Render maps that contain all resource spawns, some important items, cells and maybe a few other things.
2. Build insanely fast container/cell maps.

## How to setup:

1. Install Python
2. Open a CMD in the project root folder
3. Run `pip install -r requirements.txt`

If this command fails make sure pip installed and the environment variables are set for both Python and pip.

## How to generate container/cell maps

1. Open a CMD in the project root folder.
2. Run `python -m src.show_containers <level_name>`

Optionally you can directly specify a marker set hash and with these tags u can set which things are shown:

| Argument | Effect |
| --- | --- |
| -h | shows the help message |
| -c | disables showing containers, these are enabled by default |
| -s | shows small pickups |
| -b | shows big pickups |

## How to generate resource maps for ur current level

This works by reading the game's log file with your current level and seed. Similar to Foresight in Logger.

1. Open a CMD in the project root folder.
2. Run `python -m src.main`

From now on the app runs in the background and awaits for you to press the hotkey `ctrl-shift-a` to generate the maps for your current level. Beware some specific stuff is not shown properly. You may still need to use the Logger to see which key is for which door in some levels or terminals, hsus etc.

Optionally you can also customize the exact behaviour of this:

| Argument | Effect |
| --- | --- |
| -h | shows the help message |
| -k HOTKEY | modify the hotkey to whatever you want |
| -a | automatically render the maps when a seed is found, beware if you are resetting a lot it might cause issues with performance |

