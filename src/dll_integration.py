import ctypes
import json
import os
from ctypes import CFUNCTYPE, c_char_p, c_uint8, c_uint32, c_void_p
from pathlib import Path
from typing import Any

from src.data_loading.item_name_convert import convert_name, reset_keys
from src.data_loading.level import load_level
from src.mesh_handling.load_mesh import get_bounds_svg_multi
from src.mesh_handling.svg import add_item
from src.page_generator.open_generated import open_generated_svg
from src.show_containers import add_text

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


tracked_container_spawns = []
tracked_small_pickup_spawns = []
tracked_big_pickup_spawns = []
marker_set = 0
level_name = ""


automatic_render = False
show_key_names = True
force_dimension_render = None
counter_containers = {}


def drop_first(word_string, n: int):
    if "_" not in word_string:
        return ""  # or return word_string, depending on what you want
    return "_".join(word_string.split("_")[n:])


def get_data_from_arrs(map, overflow, counter_overflow, dimension, zone, id):
    data = None
    
    if id == -1:
        in_list_id = counter_overflow.get(dimension, {}).get(zone, 0)
        try:
            data = overflow.get(dimension, {}).get(zone, [])[in_list_id]
        except IndexError:
            data = None
        
        counter_overflow.setdefault(dimension, {})[zone] = in_list_id + 1
        
        print(f"{in_list_id}: {data}")
    else:
        data = map.get(dimension, {}).get(zone, {}).get(id, None)
    
    return data


def do_everything():
    global tracked_container_spawns, tracked_small_pickup_spawns, tracked_big_pickup_spawns
    global marker_set, level_name, counter_containers

    level_data = load_level(level_name, marker_set)
    if level_data is None:
        return

    container_map = level_data["container_map"]
    small_pickups_map = level_data["small_pickups_map"]
    big_pickups_map = level_data["big_pickups_map"]
    
    overflow_containers = level_data["overflow_containers"]
    overflow_small_pickups = level_data["overflow_small_pickups"]
    overflow_big_pickups = level_data["overflow_big_pickups"]
    
    overflow_counter_container = {}
    overflow_counter_small_pickup = {}
    overflow_counter_big_pickup = {}
    
    counter_containers = {}

    for i in range(len(level_data["dimensions_svgs"])):
        if force_dimension_render is not None and force_dimension_render != i:
            continue
        
        svg = level_data["dimensions_svgs"][i][:]
        bounds = get_bounds_svg_multi(level_data["meshes"][i])

        for item_spawn in tracked_container_spawns:
            old_name, zone, id = item_spawn
            name = convert_name(old_name)

            data = get_data_from_arrs(
                container_map, 
                overflow_containers, 
                overflow_counter_container, 
                i, 
                zone, 
                id
            )

            if data is None:
                continue
            
            if name == "consumable":
                name = drop_first(data["image"], 2)

            offset = counter_containers.get(i, {}).get(zone, {}).get(id, 0)

            counter_containers.setdefault(i, {}).setdefault(zone, {})[id] = offset + 1
            pos_x, pos_y = data["position"]
            pos_x += offset
            pos = (pos_x, pos_y)

            svg = add_item(svg, name, pos, data["rotation"], bounds)
            
            if name == "Key0":
                pos_y += 10
                svg = add_text(svg, (pos_x, pos_y), bounds, old_name, 1)
            
        for item_spawn in tracked_small_pickup_spawns:
            name, zone, id = item_spawn
            name = convert_name(name)

            data = get_data_from_arrs(
                small_pickups_map, 
                overflow_small_pickups, 
                overflow_counter_small_pickup, 
                i, 
                zone, 
                id
            )
                
            if data is None:
                continue
                
            if name == "consumable":
                name = drop_first(data["image"], 1)

            svg = add_item(svg, name, data["position"], data["rotation"], bounds)
            
        for item_spawn in tracked_big_pickup_spawns:
            name, zone, id = item_spawn
            name = convert_name(name)

            data = get_data_from_arrs(
                big_pickups_map, 
                overflow_big_pickups, 
                overflow_counter_big_pickup, 
                i, 
                zone, 
                id
            )

            if data is None:
                continue
                
            print(f"{name} spawned in {zone} at {id}")
            
            if name == "consumable":
                name = drop_first(data["image"], 1)

            svg = add_item(svg, name, data["position"], data["rotation"], bounds)

        open_generated_svg(svg, i)


# 4. Implement a Python callback function
# The callback returns a message that is based on the values
# u set when the callback is created by add_callback(...)
@CALLBACK_TYPE
def my_event_callback(_context, message):
    global tracked_container_spawns, tracked_small_pickup_spawns, tracked_big_pickup_spawns
    global marker_set, level_name, counter_containers

    if message:
        data = json.loads(message)

        if "GenerationStart" in data:
            tracked_container_spawns.clear()
            tracked_small_pickup_spawns.clear()
            tracked_big_pickup_spawns.clear()
            reset_keys()
            counter_containers = {}
            marker_set = 0
            level_name = data["GenerationStart"]

        if "Key" in data:
            name, zone, id = data["Key"]
            if name in {"ArtifactWorldspawn", "ConsumableWorldspawn"}:
                tracked_small_pickup_spawns.append((name, zone, id))
            elif name in {"Cell", "CELL"}:
                tracked_big_pickup_spawns.append((name, zone, id))
            else:
                tracked_container_spawns.append((name, zone, id))

        if "ResourcePack" in data:
            name, zone, id, _size = data["ResourcePack"]
            tracked_container_spawns.append((name, zone, id))

        if "GenerationOverflowHash" in data:
            b = bytes(data["GenerationOverflowHash"])
            hex_string = b.hex()
            marker_set = hex_string[-16:]

        if "GenerationEnd" in data:
            if automatic_render:
                do_everything()
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