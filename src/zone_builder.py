
import json
import math
from PIL import Image, ImageDraw
from typing import Dict, Any
from pathlib import Path


def load_json_data(path: str):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


door_config = load_json_data("resources/door_config.json")


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


def rotate_point_around_pivot(px, py, pivot_x, pivot_y, angle_deg):
    """
    Rotate a point (px, py) around (pivot_x, pivot_y) by angle_deg (counterclockwise)
    """
    angle_rad = math.radians(angle_deg)
    # vector from pivot to point
    dx = px - pivot_x
    dy = py - pivot_y
    # rotate vector
    rx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
    ry = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    # translate back
    return int(pivot_x + rx), int(pivot_y + ry)


def draw_item(image, item_img, item, zone_rotation):
    item_rotation = item.get("rotation", 0)
    if item_rotation != 0:
        item_img = item_img.rotate(-item_rotation, expand=True)
    
    # Original item position
    pos = item["position"]
    x = pos["x"]
    y = pos["y"]
    
    # Rotate the item around zone center
    if zone_rotation != 0:
        x, y = rotate_point_around_pivot(x, y, 512, 512, zone_rotation)
    
    # Adjust for rotated image size
    x -= item_img.width // 2
    y -= item_img.height // 2

    image.alpha_composite(item_img, (int(x), int(y)))


def build_zone(data: Dict[str, Any]) -> ZoneRender:
    img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    
    zone_rotation = data.get("rotation", 0)  # rotation of the zone

    # Draw each room layout (background)
    for layout_name in data["render"]:
        room_img = load_room_layout(layout_name)
        if zone_rotation != 0:
            room_img = room_img.rotate(-zone_rotation, expand=True)
        img.alpha_composite(room_img, (0, 0))
        
    for check in door_config.get(data["door_config"], []):
        render_doors = True
        
        for door_checked in check["include"]:
            # Check if at least one render name starts with door_checked
            if not any(render_name.startswith(door_checked) for render_name in data["render"]):
                render_doors = False
                break   # no need to check other include items
        
        if render_doors:
            door_img = load_item_image("weak_door")
            for door in check["doors"]:
                draw_item(img, door_img, door, zone_rotation)
                
    
    # Draw items (foreground)
    for item in data.get("items", []):
        item_img = load_item_image(item["image"])
        draw_item(img, item_img, item, zone_rotation)
    
    world_pos = (data["position"]["x"], data["position"]["y"])
    return ZoneRender(img, world_pos)
        
