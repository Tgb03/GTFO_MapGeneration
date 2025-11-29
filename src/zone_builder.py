
import json
from PIL import Image, ImageDraw
from typing import Dict, Any
from pathlib import Path

class ZoneRender:
    def __init__(self, image, position):
        self.image = image
        self.position = position


def load_room_layout(name: str) -> Image.Image:
    path = Path(f"resources/geos/{name}.png")
    img = Image.open(path).convert("RGBA")

    # Apply opacity
    opacity = 0.90   # 90% visible
    r, g, b, a = img.split()
    a = a.point(lambda i: int(i * opacity))

    return Image.merge("RGBA", (r, g, b, a))


def load_item_image(name: str) -> Image.Image:
    path = Path(f"resources/items/{name}.png")
    return Image.open(path).convert("RGBA")


def load_level(path: str):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data
    

def build_level(data: Dict[str, Any]) -> Image.Image:
    zone_builders = data["zone_builders"]
    
    built_zones = []   # list of (zone_image, (zone_x, zone_y))
    
    # --- Build all zones ---
    for key, zone_list in zone_builders.items():
        for zone_data in zone_list:
            zone_render = build_zone(zone_data)
            built_zones.append((zone_render.image, zone_render.position))
    
    if not built_zones:
        raise ValueError("No zones found in level data")
    
    # --- Determine final stitched image size ---
    min_x = min(pos[0] for _, pos in built_zones)
    max_x = max(pos[0] for _, pos in built_zones)
    min_y = min(pos[1] for _, pos in built_zones)
    max_y = max(pos[1] for _, pos in built_zones)
    
    width_zones = (max_x - min_x + 1)
    height_zones = (max_y - min_y + 1)
    
    final_width = width_zones * 1024
    final_height = height_zones * 1024
    
    # Create final large image
    final_img = Image.new("RGBA", (final_width, final_height), (0, 0, 0, 0))
    
    # --- Paste each zone in correct pixel position ---
    for zone_img, (zone_x, zone_y) in built_zones:
        px = (zone_x - min_x) * 1024
        py = (zone_y - min_y) * 1024
        final_img.alpha_composite(zone_img, (px, py))
    
    return final_img


def build_zone(data: Dict[str, Any]) -> ZoneRender:
    img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw each room layout (background layers)
    for layout_name in data["render"]:
        room_img = load_room_layout(layout_name)
        img.alpha_composite(room_img, (0, 0))
    
    # Draw items (foreground objects)
    for item in data.get("items", []):
        item_img = load_item_image(item["image"])

        # Rotation: Pillow rotates counterclockwise; expand keeps image bounds correct
        rotation = item.get("rotation", 0)   # if rotation is 0/90/180/270
        if rotation != 0:
            item_img = item_img.rotate(-rotation, expand=True)

        # Position
        pos = item["position"]
        x = pos["x"]
        y = pos["y"]

        img.alpha_composite(item_img, (x, y))
    
    # World position of the zone
    world_pos = (data["position"]["x"], data["position"]["y"])
    
    return ZoneRender(img, world_pos)
        
