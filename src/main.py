import argparse
from time import sleep

import keyboard

from html_server.server import app
from src import dll_integration
from src.dll_integration import do_everything, start_dll_thread
from src.page_generator import open_generated
from multiprocessing import Process


def on_hotkey():
    do_everything()
    

def run_server():
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False,
        use_reloader=False
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-k", "--hotkey", default="ctrl+shift+a", help="change hotkey for generating map")
    parser.add_argument("-a", "--automatic-render", action="store_true", default=False, help="generate map automatically when generation ends")
    parser.add_argument("-r", "--stop-automatic-reopen", action="store_false", default=True, help="stop the app from automatically reopening the generated map every time, it will open it only once and you will have to manually refresh your tab")
    parser.add_argument("-d", "--dimension-shown", default=None, help="Show only a specific dimension, first is dimension 0")
    parser.add_argument("-s", "--use-server", default=False, action="store_true", help="Render stuff on a nicer looking html server")
    parser.add_argument("-t", "--tickrate", default=2000, help="Milliseconds in between each update check for the server")

    args = parser.parse_args()
    
    open_generated.use_html_server = args.use_server
    hotkey = args.hotkey
    dll_integration.automatic_render = args.automatic_render
    open_generated.reopen = args.stop_automatic_reopen
    open_generated.tickrate = args.tickrate
    if args.use_server:
        dll_integration.automatic_render = True
    if args.dimension_shown is not None:
        dll_integration.force_dimension_render = int(args.dimension_shown)
    
    t = Process(target = run_server)
    if args.automatic_render is False:
        keyboard.add_hotkey(hotkey=hotkey, callback=on_hotkey)
    if args.use_server:
        t.start()
    
    start_dll_thread()
    while True:
        sleep(1)


if __name__ == "__main__":
    main()    
