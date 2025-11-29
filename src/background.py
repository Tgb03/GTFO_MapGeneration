from typing import Tuple
from PIL import Image, ImageDraw

spacing = 128
line_width = 4
line_color = (25, 33, 36, 255)
background_color = (17, 25, 28, 255)
crosshair_color = (31, 39, 42, 255)
crosshair_size = 5
half_width = line_width // 2

def create_background(size: Tuple[int, int]):
    # Base background (solid color)
    background = Image.new("RGBA", size, background_color)
    
    # Transparent overlay for grid lines
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw vertical lines
    for x in range(0, size[0], spacing):
        draw.rectangle([x, 0, x + line_width - 1, size[1]], fill=line_color)
    
    # Draw horizontal lines
    for y in range(0, size[1], spacing):
        draw.rectangle([0, y, size[0], y + line_width - 1], fill=line_color)
    
    # Draw crosshairs at intersections
    for x in range(0, size[0], spacing):
        for y in range(0, size[1], spacing):
            # Horizontal line
            draw.rectangle(
                [x - crosshair_size + 1, y, x + crosshair_size + half_width, y + line_width - 1],
                fill=crosshair_color
            )
            # Vertical bar
            draw.rectangle(
                [x, y - crosshair_size + 1, x + line_width - 1, y + crosshair_size + half_width],
                fill=crosshair_color
            )
    
    # Composite overlay onto background
    final = Image.alpha_composite(background, overlay)
    return final
