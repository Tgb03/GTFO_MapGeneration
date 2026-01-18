import tempfile
import webbrowser
from pathlib import Path
import time

BASE_DIR = Path(tempfile.gettempdir()) / "live_gtfo_svgs"
BASE_DIR.mkdir(exist_ok=True)
id_set = set()
reopen = True

def open_generated_svg(svg: str, id):
    svg_path = BASE_DIR / f"live_{id}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    # Cache buster so browser reloads
    url = f"file://{svg_path}?t={time.time()}"
    if reopen or id not in id_set:
        id_set.add(id)
        webbrowser.open(url)