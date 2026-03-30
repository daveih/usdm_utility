#!/usr/bin/env python3
"""
LinkedIn Tap Image Composer
────────────────────────────────────────────────────────────────
Overlays a pulsing red circular highlight onto a screenshot at
a given point and outputs a LinkedIn-ready 1200×627 image.

Usage:
    python linkedin_tap_composer.py screenshot.png
    python linkedin_tap_composer.py screenshot.png --x 420 --y 310
    python linkedin_tap_composer.py screenshot.png --x 420 --y 310 --out result.jpg

Install:
    pip install Pillow
"""

import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter


# ── Tune everything here ──────────────────────────────────────────────────────

LINKEDIN_SIZE = (1200, 627)      # LinkedIn recommended post image size

# Default tap point as fraction of image (0.0–1.0).
# Override at runtime with --x / --y pixel flags.
TAP_X_FRAC = 0.5
TAP_Y_FRAC = 0.5

# Ripple rings — (radius, stroke_width, alpha) from outermost to innermost
PULSE_COLOR = (255, 0, 0)
# Each ring: (radius, band_width, blur) — drawn on its own layer then composited
RIPPLE_RINGS = [
    (55, 14, 8),
    (32, 14, 6),
    (12, 12, 4),
]

# Inner hard dot
DOT_RADIUS = 5
DOT_COLOR  = (255, 0, 0, 255)

# Slight screen darkening so the pulse pops (0.0 = no dim, 1.0 = black)
SCREEN_DIM = 0.0

# ─────────────────────────────────────────────────────────────────────────────


def smart_crop(img: Image.Image, target: tuple) -> Image.Image:
    """Scale to fill target size, then centre-crop."""
    tw, th = target
    iw, ih = img.size
    scale  = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img    = img.resize((nw, nh), Image.LANCZOS)
    left   = (nw - tw) // 2
    top    = (nh - th) // 2
    return img.crop([left, top, left + tw, top + th])


def dim_screen(img: Image.Image, amount: float) -> Image.Image:
    """Multiply the image by (1 - amount) to subtly darken it."""
    if amount <= 0:
        return img
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * amount)))
    return Image.alpha_composite(img, overlay)


def draw_pulse(size: tuple, cx: int, cy: int) -> Image.Image:
    """Glowing red ripple — blur the alpha mask separately to avoid grey fringing."""
    r, g, b = PULSE_COLOR

    # Build a greyscale mask for all rings + dot (white = opaque)
    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)

    for radius, band_w, blur in RIPPLE_RINGS:
        ring_mask = Image.new("L", size, 0)
        rd = ImageDraw.Draw(ring_mask)
        rd.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=255,
        )
        inner = radius - band_w
        if inner > 0:
            rd.ellipse(
                [cx - inner, cy - inner, cx + inner, cy + inner],
                fill=0,
            )
        ring_mask = ring_mask.filter(ImageFilter.GaussianBlur(blur))
        # Composite: take the brighter of the two masks
        mask = ImageChops.lighter(mask, ring_mask)

    # Hard inner dot
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        [cx - DOT_RADIUS, cy - DOT_RADIUS, cx + DOT_RADIUS, cy + DOT_RADIUS],
        fill=255,
    )

    # Solid red layer masked by the blurred alpha
    colour = Image.new("RGBA", size, (r, g, b, 255))
    colour.putalpha(mask)
    return colour


def compose(
    screenshot_path: str,
    tap_x: int = None,
    tap_y: int = None,
    output_path: str = None,
) -> str:
    img = Image.open(screenshot_path).convert("RGBA")
    img = smart_crop(img, LINKEDIN_SIZE)
    img = dim_screen(img, SCREEN_DIM)

    w, h = img.size
    cx = tap_x if tap_x is not None else int(w * TAP_X_FRAC)
    cy = tap_y if tap_y is not None else int(h * TAP_Y_FRAC)

    pulse  = draw_pulse((w, h), cx, cy)
    result = Image.alpha_composite(img, pulse)

    if output_path is None:
        p = Path(screenshot_path)
        output_path = str(p.parent / f"{p.stem}_linkedin.jpg")

    result.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"✓  Saved → {output_path}")
    print(f"   Size : {w}×{h}px  |  Tap point: ({cx}, {cy})")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compose a LinkedIn image with a red pulse highlight."
    )
    parser.add_argument("screenshot", help="Path to your screenshot (PNG or JPG)")
    parser.add_argument("--x",   type=int, help="Tap X position in pixels")
    parser.add_argument("--y",   type=int, help="Tap Y position in pixels")
    parser.add_argument("--out", type=str, help="Output path (default: <name>_linkedin.jpg)")
    args = parser.parse_args()

    compose(args.screenshot, tap_x=args.x, tap_y=args.y, output_path=args.out)
