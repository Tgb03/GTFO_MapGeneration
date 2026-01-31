import argparse
from time import sleep
from multiprocessing import Process

import keyboard
import uvicorn

from html_server.server import app
from src import dll_integration
from src.dll_integration import do_everything, start_dll_thread
from src.page_generator import open_generated


def on_hotkey():
    do_everything()


def run_server(ip="127.0.0.1", port=8000):
    uvicorn.run(
        app,
        host=ip,
        port=int(port),
        log_level="info",
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-k", "--hotkey", default="ctrl+shift+a", help="change hotkey for generating map")
    parser.add_argument("-a", "--automatic-render", action="store_true", default=False, help="generate map automatically when generation ends")
    parser.add_argument("-r", "--stop-automatic-reopen", action="store_false", default=True, help="stop the app from automatically reopening the generated map every time, it will open it only once and you will have to manually refresh your tab")
    parser.add_argument("-d", "--dimension-shown", default=None, help="Show only a specific dimension, first is dimension 0")
    parser.add_argument("-s", "--use-server", default=False, action="store_true", help="Render stuff on a nicer looking html server")
    parser.add_argument("-p", "--port", default=8000, help="Port used by the server")
    parser.add_argument("--ip", default="127.0.0.1", help="IP used by the server")

    args = parser.parse_args()

    open_generated.port = args.port
    open_generated.use_html_server = args.use_server
    open_generated.reopen = args.stop_automatic_reopen
    if args.use_server:
        dll_integration.automatic_render = True
    if args.dimension_shown is not None:
        dll_integration.force_dimension_render = int(args.dimension_shown)

    # Start FastAPI server in a separate process
    server_process = None
    if args.use_server:
        server_process = Process(target=run_server, args=(args.ip, args.port))
        server_process.daemon = True
        server_process.start()

    # Hotkey only if not automatic
    if not args.automatic_render:
        keyboard.add_hotkey(hotkey=args.hotkey, callback=on_hotkey)

    # Start DLL thread
    start_dll_thread()

    print("Main loop running. Press Ctrl+C to exit.")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        if server_process:
            server_process.terminate()


if __name__ == "__main__":
    main()
