from PIL import Image
import background
from zone_builder import build_level, load_json_data

test_data = load_json_data("resources/levels/r1a1.json")
door_config = load_json_data("resources/door_config.json")

result = build_level(test_data)
bg = background.create_background(result.size)

bg.alpha_composite(result, (0, 0))
final_img = bg

print("done generating")

final_img.show()
