import argparse
import os

from src.data_loading.item import load_item_svg
from src.data_loading.level import load_level
from src.mesh_handling.load_mesh import get_bounds_svg_multi, to_svg_pos
from src.mesh_handling.svg import add_item, extract_inner_svg
from src.page_generator.open_generated import open_generated_svg


def list_level_markers(level_name):
    matches = []

    for filename in os.listdir("resources/levels"):
        if filename.startswith(level_name):
            matches.append(filename)

    return matches


def extract_marker(filename):
    name, _ = os.path.splitext(filename)
    marker = name.split("_")[-1]
    return marker


def choose_marker(level_name):
    files = list_level_markers(level_name)

    if not files:
        print("No matching levels found.")
        return None

    print("Available versions:")
    for i, filename in enumerate(files, start=1):
        print(f"{i}) {filename}")

    while True:
        try:
            choice = int(input("Choose a version number: "))
            if 1 <= choice <= len(files):
                chosen_file = files[choice - 1]
                return extract_marker(chosen_file)
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")


def add_text(svg, pos, bounds, text, text_size):
    (pos_x, pos_y) = pos

    try:
        item_svg = load_item_svg("text")
        inner = extract_inner_svg(item_svg)
        inner = inner.format(text=text, size=str(text_size))

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
    parser = argparse.ArgumentParser()
    parser.add_argument("level_name")
    parser.add_argument("marker", type=str, nargs="?", default=0)

    parser.add_argument("-c", "--container-show", action="store_false", default=True, help="stop showing containers")
    parser.add_argument("-s", "--small-pickup-show", action="store_true", default=False, help="show small pickups")
    parser.add_argument("-b", "--big-pickup-show", action="store_true", default=False, help="show big pickups")
    parser.add_argument("-t", "--text-size", type=float, nargs="?", default=1, help="change the text size")
    parser.add_argument("-i", "--hide-images", action="store_true", default=False, help="Hide images and just put the text where the container is")

    args = parser.parse_args()
    
    level_name = args.level_name.upper()
    marker = args.marker
    
    show_containers = args.container_show
    show_small_pickups = args.small_pickup_show
    show_big_pickups = args.big_pickup_show
    text_size = args.text_size
    hide_images = args.hide_images

    level_data = load_level(level_name, marker)
    if level_data is None:
        print("Failed to load level data")
        marker = choose_marker(level_name)
        level_data = load_level(level_name, marker)
        
    if level_data is None:
        print("Failed to find level_name or marker is incorrect")
        return

    container_map = level_data["container_map"]
    small_pickups_map = level_data["small_pickups_map"]
    big_pickups_map = level_data["big_pickups_map"]

    for i in range(len(level_data["dimensions_svgs"])):
        svg = level_data["dimensions_svgs"][i][:]
        bounds = get_bounds_svg_multi(level_data["meshes"][i])

        if show_containers:
            for _, containers_in_zone in container_map.get(i, {}).items():
                for id, container in containers_in_zone.items():
                    pos = container["position"]
                    name = container["image"].split("_")[0]
    
                    if not hide_images:
                        svg = add_item(svg, name, pos, 0, bounds)
                        pos = (pos[0], pos[1] + 1)
                    
                    pos = (pos[0], pos[1] + 9)
                    svg = add_text(svg, pos, bounds, str(id), text_size)

        if show_small_pickups:
            for _, small_pickups_in_zone in small_pickups_map.get(i, {}).items():
                for id, pickup in small_pickups_in_zone.items():
                    pos = pickup["position"]
                    name = "small_pickup"
    
                    if not hide_images:
                        svg = add_item(svg, name, pos, 0, bounds)
                        pos = (pos[0], pos[1] + 1)
                        
                    pos = (pos[0], pos[1] + 9)
                    svg = add_text(svg, pos, bounds, str(id), text_size)

        if show_big_pickups:
            for _, big_pickups_in_zone in big_pickups_map.get(i, {}).items():
                for id, pickup in big_pickups_in_zone.items():
                    pos = pickup["position"]
                    name = "big_pickup"
    
                    if not hide_images:
                        svg = add_item(svg, name, pos, 0, bounds)
                        pos = (pos[0], pos[1] + 1)
                        
                    pos = (pos[0], pos[1] + 9)
                    svg = add_text(svg, pos, bounds, str(id), text_size)

        open_generated_svg(svg, i)


if __name__ == "__main__":
    main()
