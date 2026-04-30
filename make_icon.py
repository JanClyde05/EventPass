"""
EventPass v2 — Icon Generator
Run: python make_icon.py
Requires: pip install pillow

Design:
  Dark (#0a0c0f) rounded square tile.
  Seven vertical barcode bars in accent green (#00e5a0),
  varying widths — reads as a badge/ticket scanner icon at all sizes.
  A thin horizontal scan-line below the bars.
  No gradients. No 3D. Flat and clean.
"""

from PIL import Image, ImageDraw


# ── Colour palette (matches EventPass CSS variables) ────────────────────────
BG      = (10,  12,  15,  255)   # --bg       #0a0c0f
SURFACE = (17,  20,  25,  255)   # --surface  #111419
BORDER  = (37,  42,  53,  255)   # --border   #252a35
ACCENT  = (0,  229, 160,  255)   # --accent   #00e5a0
ACCENT_DIM = (0, 229, 160, 128)  # accent at 50% opacity (scan line)


def make_frame(size: int) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    # ── Background tile with rounded corners ─────────────────────────────────
    radius = max(2, size // 5)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)

    # ── Subtle border ─────────────────────────────────────────────────────────
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius,
                        outline=BORDER, width=max(1, size // 64))

    # ── Barcode bars ─────────────────────────────────────────────────────────
    # Seven bars with varying widths (relative units).
    # Pattern mimics a real Code 128 quiet zone: narrow · wide · narrow etc.
    pattern = [3, 1, 4, 1, 3, 1, 4]   # relative bar widths

    # Scale unit so bars fill ~75% of icon width
    total_units = sum(pattern) + len(pattern) - 1   # bars + 1-unit gaps between
    unit   = max(1, int(size * 0.72 / total_units))
    gap    = unit                                     # gap between bars

    bar_h  = int(size * 0.44)
    bar_y0 = int(size * 0.22)
    bar_y1 = bar_y0 + bar_h - 1

    total_px = sum(w * unit for w in pattern) + gap * (len(pattern) - 1)
    x = (size - total_px) // 2

    for bw in pattern:
        w_px = bw * unit
        d.rectangle([x, bar_y0, x + w_px - 1, bar_y1], fill=ACCENT)
        x += w_px + gap

    # ── Scan line (thin horizontal rule below bars) ───────────────────────────
    line_y = bar_y1 + max(2, size // 24)
    lx0    = (size - total_px) // 2
    lx1    = lx0 + total_px - 1
    lh     = max(1, size // 48)
    d.rectangle([lx0, line_y, lx1, line_y + lh - 1], fill=ACCENT_DIM)

    return img


def main():
    sizes  = [256, 128, 64, 48, 32, 16]
    frames = [make_frame(s) for s in sizes]

    # Save as multi-size .ico
    frames[0].save(
        'icon.ico',
        format       = 'ICO',
        sizes        = [(s, s) for s in sizes],
        append_images = frames[1:],
    )

    # Also save a 256 PNG for preview / macOS .icns pipeline
    frames[0].save('icon_256.png', format='PNG')

    print('✓  icon.ico    created  (sizes: ' + ', '.join(str(s) for s in sizes) + ')')
    print('✓  icon_256.png created  (256×256 preview)')


if __name__ == '__main__':
    main()
