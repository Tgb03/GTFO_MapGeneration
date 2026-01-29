import xml.etree.ElementTree as ET

from src.data_loading.item import load_item_svg
from src.mesh_handling.background import apply_grid_background
from src.mesh_handling.load_mesh import get_bounds_svg_multi, meshes_to_merged_svg, to_svg_pos
import re


item_svg_buffer = {}


def extract_scale(path_svg):
    match = re.search(r'transform="[^"]*scale\(([^,]+),\s*([^)]+)\)"', path_svg)
    if not match:
        return 1.0, 1.0

    sx = float(match.group(1))
    sy = float(match.group(2))
    return sx, sy


def inline_fill(svg_fragment):
    # Find .st0 { fill:#xxxxxx; }
    match = re.search(r'\.st0\s*{\s*fill\s*:\s*([^;]+);', svg_fragment)
    if not match:
        return svg_fragment
    
    fill_color = match.group(1).strip()

    # Apply fill="..." to any path with class="st0"
    svg_fragment = re.sub(
        r'<path([^>]+)class="st0"([^>]*)>',
        rf'<path\1\2 fill="{fill_color}">',
        svg_fragment
    )

    # Remove the style block entirely
    svg_fragment = re.sub(r'<style[\s\S]*?</style>', '', svg_fragment)

    return svg_fragment
    

def strip_ns(elem):
    for el in elem.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]
    return elem    


def extract_inner_svg(svg_text: str) -> str:
    """
    Extracts everything *inside* the outer <svg>...</svg> element.
    Returns the children as a single concatenated string.
    """
    # Parse SVG
    root = ET.fromstring(svg_text)
    strip_ns(root)

    # Get children XML as string
    inner_parts = []
    for child in root:
        inner_parts.append(ET.tostring(child, encoding="unicode"))

    return "".join(inner_parts)


def get_svg(meshes, item_descriptors):
    bounds = get_bounds_svg_multi(meshes)

    svg = meshes_to_merged_svg(meshes)
    svg = apply_grid_background(svg)
    return add_static_items(svg, item_descriptors, bounds)
    

def add_item(svg, item_name, pos, rotation, bounds):
    (pos_x, pos_y) = pos

    try:
        if item_name not in item_svg_buffer:
            item_svg = load_item_svg(item_name)
            inner = extract_inner_svg(item_svg)
            item_svg_buffer[item_name] = inner

        if item_svg_buffer[item_name] is None:
            return svg

        pos_x, pos_y = to_svg_pos([pos_x, pos_y], bounds[0][0], bounds[1][1])
        
        group = f"""
        <g transform="translate({pos_x}, {pos_y}) rotate({rotation})">
            {item_svg_buffer[item_name]}
        </g>
        """

        svg = svg.replace("</svg>", group + "</svg>")
    except Exception as e:
        item_svg_buffer[item_name] = None
        print(e)

    return svg


def add_static_items(svg, item_descriptors, bounds):
    for item in item_descriptors:
        svg = add_item(svg, item["image"], item["position"], item["rotation"], bounds)

    return svg
