from PIL import Image
import background
from zone_builder import build_level, load_level

test_data = load_level("resources/levels/test.json")

result = build_level(test_data)
bg = background.create_background(result.size)

bg.alpha_composite(result, (0, 0))
final_img = bg

final_img.show()
