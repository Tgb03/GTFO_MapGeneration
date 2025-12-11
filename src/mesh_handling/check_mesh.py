import tempfile
import webbrowser

from src.data_loading.deserializer import load_data_binary
from src.mesh_handling.svg import get_svg

result = load_data_binary("resources/levels/R8E3_7.bin")
if result is None:
    print("Failed to parse binary file")
    exit()

items = result["static_items"][0]
result = result["meshes"][0]

verts = result["vertices"]
tris = result["triangles"]

print(verts.shape, tris.shape)
verts = verts.copy()
verts[:, 1] = 0.0

# show_mesh(verts, tris)

svg = get_svg(verts, tris)

print("started writing")

# Create a temporary SVG file
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
tmp.write(svg.encode("utf-8"))
tmp.close()

# Open it in the default web browser
webbrowser.open("file://" + tmp.name)
