from time import sleep

import keyboard

from src.dll_integration import do_everything, start_dll_thread


def on_hotkey():
    do_everything()


keyboard.add_hotkey("ctrl+shift+a", on_hotkey)


start_dll_thread()
while True:
    sleep(1)
