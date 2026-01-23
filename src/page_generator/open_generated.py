import tempfile
import webbrowser
from pathlib import Path
import time
import requests

use_html_server = False
reopen = True
tickrate = 2000
ip = "127.0.0.1"
port = 8000

BASE_DIR = Path(tempfile.gettempdir()) / "live_gtfo_svgs"
BASE_DIR.mkdir(exist_ok=True)
id_set = set()

def open_generated_svg(svg: str, id):
    if use_html_server:
        if id not in id_set:
            id_set.add(id)
            webbrowser.open(f"http://{ip}:{port}/?id={id}&tickrate={tickrate}")
        requests.post(f"http://{ip}:{port}/svg/{id}", data=svg)
        return
        
    svg_path = BASE_DIR / f"live_{id}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    url = f"file://{svg_path}?t={time.time()}"
    if reopen or id not in id_set:
        id_set.add(id)
        webbrowser.open(url)