import ctypes
import json
import os
import webbrowser
from ctypes import CFUNCTYPE, c_char_p, c_uint8, c_uint32, c_void_p
from pathlib import Path
from typing import Any

from PIL.Image import tempfile

from src.data_loading.item_name_convert import convert_name, reset_keys
from src.data_loading.level import load_level
from src.mesh_handling.load_mesh import get_bounds_svg
from src.mesh_handling.svg import add_item

dll_relative_path = "../resources/gtfo_log_reader_core_64bit.dll"
log_folder_path = str(
    os.path.join(
        os.getenv("USERPROFILE"),
        "AppData",
        "LocalLow",
        "10 Chambers Collective",
        "GTFO",
    )
)

script_dir = Path(__file__).resolve().parent
dll_path = os.path.join(script_dir, dll_relative_path)
# Replace with actual DLL name
lib = ctypes.CDLL(dll_path)

id_to_item_name = {
    "Healthpack": "medi",
    "Ammopack": "ammo",
    "ToolRefillpack": "tool",
    "ArtifactContainer": "arti",
    "ConsumableContainer": "cons",
}

# 2. Define callback type: extern "C" fn(context: *const c_void, message: *const c_char)
CALLBACK_TYPE = CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)

# 3. Define Rust function signatures

# void start_listener(const char* file_path)
lib.start_listener.argtypes = [c_char_p]
lib.start_listener.restype = None

# void add_callback(uint8_t code, uint8_t message_type, uint32_t channel_id, void* context, void* callback)
lib.add_callback.argtypes = [c_uint8, c_uint8, c_uint32, c_void_p, c_void_p]
lib.add_callback.restype = None

# void remove_callback(uint32_t channel_id)
lib.remove_callback.argtypes = [c_uint8, c_uint32]
lib.remove_callback.restype = None


tracked_spawns = []
marker_set = 0
level_name = ""


counter_containers = {}


def do_everything():
    global tracked_spawns, marker_set, level_name, counter_containers

    level_data = load_level(level_name, marker_set)
    if level_data is None:
        return

    container_map = level_data["container_map"]

    for i in range(len(level_data["dimensions_svgs"])):
        svg = level_data["dimensions_svgs"][i][:]
        verts = level_data["meshes"][i]["vertices"]
        tris = level_data["meshes"][i]["triangles"]
        bounds = get_bounds_svg(verts, tris)

        for item_spawn in tracked_spawns:
            name, zone, id = item_spawn
            name = convert_name(name)

            data = container_map.get(i, {}).get(zone, {}).get(id, None)

            if data is None:
                continue

            offset = counter_containers.get(i, {}).get(zone, {}).get(id, 0)

            counter_containers.setdefault(i, {}).setdefault(zone, {})[id] = offset + 1
            pos_x, pos_y = data["position"]
            pos_x += offset
            pos = (pos_x, pos_y)

            svg = add_item(svg, name, pos, data["rotation"], bounds)

        # Create a temporary SVG file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
        tmp.write(svg.encode("utf-8"))
        tmp.close()

        # Open it in the default web browser
        webbrowser.open("file://" + tmp.name)


def add_to_tracked(name, zone, id):
    global tracked_spawns

    tracked_spawns.append((name, zone, id))


# 4. Implement a Python callback function
# The callback returns a message that is based on the values
# u set when the callback is created by add_callback(...)
@CALLBACK_TYPE
def my_event_callback(_context, message):
    global tracked_spawns, marker_set, level_name, counter_containers

    if message:
        data = json.loads(message)

        if "GenerationStart" in data:
            tracked_spawns.clear()
            reset_keys()
            counter_containers = {}
            marker_set = 0
            level_name = data["GenerationStart"]

        if "Key" in data:
            name, zone, id = data["Key"]
            add_to_tracked(name, zone, id)

        if "ResourcePack" in data:
            name, zone, id, _size = data["ResourcePack"]
            add_to_tracked(name, zone, id)

        if "GenerationOverflow" in data:
            marker_set = data["GenerationOverflow"]

        if "GenerationEnd" in data:
            # do_everything()
            pass


def start_dll_thread():
    # Add a callback with dummy values
    code = 4  # e.g., SubscribeCode::Tokenizer
    msg_type = 1  # e.g., SubscriptionType::JSON
    channel_id = 1  # your app-defined channel ID
    callback_fn_ptr = ctypes.cast(my_event_callback, c_void_p)

    lib.add_callback(code, msg_type, channel_id, 0, callback_fn_ptr)

    # Start the listener thread
    lib.start_listener(log_folder_path.encode("utf-8"))
