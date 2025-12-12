import argparse
from time import sleep

import keyboard

from src import dll_integration
from src.dll_integration import do_everything, start_dll_thread


def on_hotkey():
    do_everything()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-k", "--hotkey", default="ctrl+shift+a", help="change hotkey for generating map")
    parser.add_argument("-a", "--automatic-render", action="store_true", default=False, help="generate map automatically when generation ends")

    args = parser.parse_args()
    
    hotkey = args.hotkey
    dll_integration.automatic_render = args.automatic_render
    
    keyboard.add_hotkey(hotkey=hotkey, callback=on_hotkey)
    
    start_dll_thread()
    while True:
        sleep(1)


if __name__ == "__main__":
    main()    
