import sys
import webbrowser

from PIL.Image import tempfile

from src.data_loading.item import load_item_svg
from src.data_loading.level import load_level
from src.mesh_handling.load_mesh import get_bounds_svg, to_svg_pos
from src.mesh_handling.svg import add_item, extract_inner_svg


def add_text(svg, pos, bounds, text):
    (pos_x, pos_y) = pos

    try:
        item_svg = load_item_svg("text")
        inner = extract_inner_svg(item_svg)
        inner = inner.format(text=text)

        pos_x, pos_y = to_svg_pos([pos_x, pos_y], bounds[0][0], bounds[1][1])

        group = f"""
        <g transform="translate({pos_x}, {pos_y}) rotate(0)">
            {inner}
        </g>
        """

        svg = svg.replace("</svg>", group + "</svg>")
    except Exception as e:
        print(f"got error: {e}")

    return svg


def main():
    if len(sys.argv) < 2:
        print("No level name provided.")
        return

    level_name = sys.argv[1]
    marker = 0
    if len(sys.argv) >= 3:
        try:
            value = int(sys.argv[2])
            if value >= 0:
                marker = value
        except ValueError:
            pass  # keep default 0 if conversion fails

    level_data = load_level(level_name, marker)
    if level_data is None:
        return

    container_map = level_data["container_map"]

    for i in range(len(level_data["dimensions_svgs"])):
        svg = level_data["dimensions_svgs"][i][:]
        verts = level_data["meshes"][i]["vertices"]
        tris = level_data["meshes"][i]["triangles"]
        bounds = get_bounds_svg(verts, tris)

        for _, containers_in_zone in container_map.get(i, {}).items():
            for id, container in containers_in_zone.items():
                pos = container["position"]
                name = container["image"]

                svg = add_item(svg, name, pos, 0, bounds)
                pos = (pos[0], pos[1] + 10)
                svg = add_text(svg, pos, bounds, str(id))

        # Create a temporary SVG file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
        tmp.write(svg.encode("utf-8"))
        tmp.close()

        # Open it in the default web browser
        webbrowser.open("file://" + tmp.name)


if __name__ == "__main__":
    main()
