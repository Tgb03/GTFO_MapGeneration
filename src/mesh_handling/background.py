import re

spacing = 6.4
line_width = spacing / 32
crosshair_size = 5 * 6.4 / 128


def apply_grid_background(svg_text):
    """
    Apply a repeating grid background to an SVG and anchor the pattern
    to the actual viewBox so it tiles correctly over negative coordinates.
    """

    # --- Extract viewBox (required for correct pattern tiling) ---
    m = re.search(r'viewBox\s*=\s*"([^"]+)"', svg_text)
    if m:
        vb = list(map(float, m.group(1).split()))
        view_min_x, view_min_y, view_w, view_h = vb
    else:
        # Fallback: assume 0 0 origin
        view_min_x = 0
        view_min_y = 0

    # --- Ensure xmlns exists ---
    def fix_xmlns(match):
        svg_tag = match.group(0)
        if "xmlns=" not in svg_tag:
            return svg_tag[:-1] + " xmlns='http://www.w3.org/2000/svg'>"
        return svg_tag

    svg_text = re.sub(r"<svg[^>]*>", fix_xmlns, svg_text, count=1)

    # --- Pattern definition aligned to viewBox origin ---
    pattern_svg = f"""
  <defs>
    <pattern id="gridPattern"
             x="{view_min_x}"
             y="{view_min_y}"
             width="{spacing}" height="{spacing}"
             patternUnits="userSpaceOnUse"
             overflow="visible">

      <rect width="100%" height="100%" fill="rgb(17,25,28)" />

      <!-- Vertical grid line -->
      <rect x="0" y="0" width="{line_width}" height="{spacing}" fill="rgb(25,33,36)" />

      <!-- Horizontal grid line -->
      <rect x="0" y="0" width="{spacing}" height="{line_width}" fill="rgb(25,33,36)" />

      <!-- Crosshair horizontal -->
      <rect x="-5" y="0" width="14" height="{line_width}" fill="rgb(31,39,42)" />

      <!-- Crosshair vertical -->
      <rect x="0" y="-5" width="{line_width}" height="14" fill="rgb(31,39,42)" />

    </pattern>
  </defs>
"""

    # --- Insert pattern + background rectangle ---
    insertion = (
        pattern_svg
        + "\n  <rect width='100%' height='100%' fill='url(#gridPattern)'/>\n"
    )

    svg_text = re.sub(
        r"(<svg[^>]*>)", lambda m: m.group(1) + insertion, svg_text, count=1
    )

    return svg_text
