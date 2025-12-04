from pathlib import Path


def load_item_svg(name: str) -> str:
    path = Path(f"resources/items/{name}.svg")
    with path.open("r", encoding="utf-8") as f:
        return f.read()
