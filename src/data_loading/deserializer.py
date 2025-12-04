import struct
from pathlib import Path

import numpy as np


# Helper to read a 7-bit prefixed string from C# BinaryWriter
def read_cs_string(f):
    # Read the length (7-bit encoded int)
    shift = 0
    result = 0
    while True:
        b = f.read(1)
        if not b:
            raise EOFError("Unexpected EOF while reading string length")
        byte = b[0]
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    length = result
    # Read the string bytes
    string_bytes = f.read(length)
    return string_bytes.decode("utf-8")


def load_data_binary(path: str):
    path = Path(path)

    try:
        with open(path, "rb") as f:
            mesh_count = struct.unpack("<i", f.read(4))[0]
            meshes = []

            # print(f"Got {mesh_count} dimensions to parse")

            for _ in range(mesh_count):
                # ---- Mesh Vertex Count ----
                verts_len = struct.unpack("<i", f.read(4))[0]
                tris_len = struct.unpack("<i", f.read(4))[0]

                # print(f"decoding size: {verts_len} and {tris_len}")

                # ---- Vertices ----
                vertices = np.frombuffer(
                    f.read(verts_len * 3 * 4),
                    dtype="<f4",  # little-endian float32
                ).reshape(verts_len, 3)

                # print("decoded vertices")

                tri_data = f.read(tris_len * 4)
                if len(tri_data) != tris_len * 4:
                    raise EOFError("Unexpected EOF reading triangles")

                triangles = np.frombuffer(tri_data, dtype="<i4")
                if triangles.size % 3 == 0:
                    triangles = triangles.reshape(-1, 3)

                # print("decoded triangles")

                # ---- Normals ----
                has_normals = struct.unpack("<?", f.read(1))[0]
                normals = (
                    [struct.unpack("<fff", f.read(12)) for _ in range(verts_len)]
                    if has_normals
                    else None
                )

                # print(f"decoded normals: {has_normals}")

                # ---- UVs ----
                has_uvs = struct.unpack("<?", f.read(1))[0]
                uvs = (
                    [struct.unpack("<ff", f.read(8)) for _ in range(verts_len)]
                    if has_uvs
                    else None
                )

                # print(f"decoded uvs: {has_uvs}")

                meshes.append(
                    {
                        "vertices": vertices,
                        "triangles": triangles,
                        "normals": normals,
                        "uvs": uvs,
                    }
                )

            # print("ended meshes")

            # ---- Nested Dictionary ----
            dimension_containers = {}
            dimensions_count = struct.unpack("<i", f.read(4))[0]
            # print(f"dimensions count: {dimensions_count}")
            out_key = struct.unpack("<i", f.read(4))[0]

            for _ in range(dimensions_count):
                outer_count = struct.unpack("<i", f.read(4))[0]
                container_map = {}

                # print(f"   zone count: {outer_count}")

                for _ in range(outer_count):
                    outer_key = struct.unpack("<i", f.read(4))[0]
                    inner_count = struct.unpack("<i", f.read(4))[0]
                    inner_dict = {}

                    # print(f"       boxes in zone count: {inner_count}")

                    for _ in range(inner_count):
                        ik_bytes = f.read(4)
                        if len(ik_bytes) != 4:
                            raise EOFError("Unexpected EOF while reading inner_key")
                        inner_key = struct.unpack("<i", ik_bytes)[0]

                        # ---- read ContainerDescriptor in the order you provided ----
                        # bw.Write(cd.image);
                        cd_image = read_cs_string(f)

                        # bw.Write(cd.position.x);
                        px_bytes = f.read(4)
                        if len(px_bytes) != 4:
                            raise EOFError("Unexpected EOF while reading position.x")
                        pos_x = struct.unpack("<f", px_bytes)[0]

                        # bw.Write(cd.position.y);
                        py_bytes = f.read(4)
                        if len(py_bytes) != 4:
                            raise EOFError("Unexpected EOF while reading position.y")
                        pos_y = struct.unpack("<f", py_bytes)[0]

                        # bw.Write(cd.rotation);
                        rot_bytes = f.read(4)
                        if len(rot_bytes) != 4:
                            raise EOFError("Unexpected EOF while reading rotation")
                        rotation = struct.unpack("<i", rot_bytes)[0]

                        inner_dict[inner_key] = {
                            "image": cd_image,
                            "position": (pos_x, pos_y),
                            "rotation": rotation,
                        }

                    container_map[outer_key] = inner_dict

                dimension_containers[out_key] = container_map

            statics_dimensions_count = struct.unpack("<i", f.read(4))[0]
            static_items = []

            # print(f"statics dimensions count: {statics_dimensions_count}")

            for _ in range(statics_dimensions_count):
                statics_count = struct.unpack("<i", f.read(4))[0]
                statics_arr = []

                # print(f"   statics in dim count: {statics_count}")

                for _ in range(statics_count):
                    # bw.Write(cd.image);
                    cd_image = read_cs_string(f)

                    # bw.Write(cd.position.x);
                    px_bytes = f.read(4)
                    if len(px_bytes) != 4:
                        raise EOFError("Unexpected EOF while reading position.x")
                    pos_x = struct.unpack("<f", px_bytes)[0]

                    # bw.Write(cd.position.y);
                    py_bytes = f.read(4)
                    if len(py_bytes) != 4:
                        raise EOFError("Unexpected EOF while reading position.y")
                    pos_y = struct.unpack("<f", py_bytes)[0]

                    # bw.Write(cd.rotation);
                    rot_bytes = f.read(4)
                    if len(rot_bytes) != 4:
                        raise EOFError("Unexpected EOF while reading rotation")
                    rotation = struct.unpack("<i", rot_bytes)[0]

                    statics_arr.append(
                        {
                            "image": cd_image,
                            "position": (pos_x, pos_y),
                            "rotation": rotation,
                        }
                    )

                static_items.append(statics_arr)

            return {
                "meshes": meshes,
                "container_map": dimension_containers,
                "static_items": static_items,
            }

    except Exception as e:
        print(e)
        # If *anything* is wrong (parsing, unexpected EOF, wrong format)
        return None
