import struct
from pathlib import Path

import numpy as np
from lxml import etree
from shapely.geometry import Polygon
from shapely.ops import unary_union

SIDE_BUFFERS = 5


def load_unity_mesh_binary(path):
    print(Path(path).absolute())

    with open(path, "rb") as f:
        vertex_count, index_count = struct.unpack("ii", f.read(8))

        vertices = np.frombuffer(
            f.read(vertex_count * 3 * 4),  # 4 bytes per float32
            dtype=np.float32,
        ).reshape(vertex_count, 3)

        triangles = np.frombuffer(f.read(index_count * 4), dtype=np.int32).reshape(
            -1, 3
        )

        # Read normals if included
        has_normals = struct.unpack("?", f.read(1))[0]
        normals = None
        if has_normals:
            normals = np.frombuffer(
                f.read(vertex_count * 3 * 4), dtype=np.float32
            ).reshape(vertex_count, 3)

        # Read UVs if included
        has_uvs = struct.unpack("?", f.read(1))[0]
        uvs = None
        if has_uvs:
            uvs = np.frombuffer(f.read(vertex_count * 2 * 4), dtype=np.float32).reshape(
                vertex_count, 2
            )

    return vertices, triangles, normals, uvs


def get_bounds_svg(vertices, triangles):
    pts_2d = vertices[:, [0, 2]].astype(float)

    min_xy = pts_2d.min(axis=0)
    max_xy = pts_2d.max(axis=0)

    return [min_xy, max_xy]


def to_svg_pos(p, lower_x_bound, upper_y_bound):
    x = SIDE_BUFFERS + p[0] - lower_x_bound
    y = SIDE_BUFFERS + upper_y_bound - p[1]  # flip inside bounding box
    return (x, y)


def mesh_to_merged_svg(vertices, triangles, svg_size=(1000, 1000), margin=10):
    """
    Convert triangle mesh directly to merged SVG without intermediate SVG text.
    """

    # ---- Project XZ plane ----
    pts_2d = vertices[:, [0, 2]].astype(float)

    # ---- Fit to SVG ----
    min_xy = pts_2d.min(axis=0)
    max_xy = pts_2d.max(axis=0)
    span = max_xy - min_xy
    span[span == 0] = 1

    width = max_xy[0] - min_xy[0]
    height = max_xy[1] - min_xy[1]

    # ---- Collect triangles as shapely polygons ----
    polys = []
    for a, b, c in triangles:
        pa = to_svg_pos(pts_2d[a], min_xy[0], max_xy[1])
        pb = to_svg_pos(pts_2d[b], min_xy[0], max_xy[1])
        pc = to_svg_pos(pts_2d[c], min_xy[0], max_xy[1])
        polys.append(Polygon([pa, pb, pc]))

    # ---- Merge all triangles ----
    merged = unary_union(polys)

    # ---- Normalize to list of polygons ----
    if merged.geom_type == "Polygon":
        merged_polys = [merged]
    else:
        merged_polys = list(merged.geoms)

    # ---- Build SVG ----
    NSMAP = {None: "http://www.w3.org/2000/svg"}
    root = etree.Element(
        "svg",
        nsmap=NSMAP,
        viewBox=f"0 0 {width + SIDE_BUFFERS * 2} {height + SIDE_BUFFERS * 2}",
        overflow="visible",
    )

    for poly in merged_polys:
        # exterior
        ext = poly.exterior.coords
        cmds = [f"M {x},{y}" for x, y in [ext[0]]]
        cmds += [f"L {x},{y}" for x, y in ext[1:]]
        cmds.append("Z")

        # holes
        for interior in poly.interiors:
            coords = interior.coords
            cmds.append(f"M {coords[0][0]},{coords[0][1]}")
            cmds += [f"L {x},{y}" for x, y in coords[1:]]
            cmds.append("Z")

        d = " ".join(cmds)
        etree.SubElement(root, "path", d=d, fill="rgb(47,61,68)")

    return etree.tostring(root, pretty_print=True).decode("utf-8")
