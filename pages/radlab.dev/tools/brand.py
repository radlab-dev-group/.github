"""Prepare the RadLab brand assets for both themes.

The original logo is a black wordmark with a warm orange-to-red gradient circle.
On the dark theme the black half disappears, and CSS `filter: invert()` would
invert the brand colours along with it. So the two variants are produced
separately: near-black pixels are recoloured to the light token while every
saturated pixel -- the gradient, the red -- is left exactly as designed.

The circle is also rebuilt as clean vector/raster art from the stops sampled off
the master, because the WordPress "circle" crop that used to stand in for a
favicon is a square crop of the full lockup and carries letters of the wordmark
across it. Sampling keeps this file honest: change the logo upstream, re-run, and
the orb, the favicon and the Open Graph card follow the new colours on their own.

    python3 tools/brand.py

Source files are fetched from the running site; they are not in this repo.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img"
TMP = Path("/tmp/radlab_brand")

SOURCE = "https://radlab.dev/wp-content/uploads/2024/04/cropped-cropped-cropped-radlab-logo-scaled-2.png"

# A pixel counts as "the black wordmark" when it is dark and barely tinted.
BLACK_LUMINANCE = 90
BLACK_SATURATION = 40
DARK_THEME_WORDMARK = (242, 242, 244)
APPLE_TILE = (14, 15, 18)          # matches --bg of the dark theme
OG_SIZE = (1200, 630)


def fetch(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        dest.write_bytes(response.read())
    return dest


def recolour_dark_parts(image: Image.Image, replacement: tuple[int, int, int]) -> Image.Image:
    """Swap the black wordmark for a light one, keep the brand gradient intact."""
    rgba = image.convert("RGBA")
    updated = []
    for red, green, blue, alpha in rgba.getdata():
        luminance = 0.299 * red + 0.587 * green + 0.114 * blue
        spread = max(red, green, blue) - min(red, green, blue)
        if luminance < BLACK_LUMINANCE and spread < BLACK_SATURATION:
            updated.append((*replacement, alpha))
        else:
            updated.append((red, green, blue, alpha))
    out = Image.new("RGBA", rgba.size)
    out.putdata(updated)
    return out


# --------------------------------------------------------------- the circle

def is_brand(pixel: tuple[int, int, int, int]) -> bool:
    """A pixel of the gradient orb: coloured enough and not near-black."""
    red, green, blue, alpha = pixel
    if alpha < 200:
        return False
    return (max(red, green, blue) - min(red, green, blue)) > 40


def circle_geometry(master: Image.Image) -> tuple[int, int, int]:
    """Centre and radius of the orb, read off the saturated pixels."""
    pixels = master.convert("RGBA").load()
    xs: list[int] = []
    ys: list[int] = []
    for x in range(master.width):
        for y in range(0, master.height, 2):
            if is_brand(pixels[x, y]):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("no brand-coloured pixels found in the source logo")
    radius = round(((max(xs) - min(xs)) / 2 + (max(ys) - min(ys)) / 2) / 2)
    return round((min(xs) + max(xs)) / 2), round((min(ys) + max(ys)) / 2), radius


def gradient_stops(master: Image.Image, centre_x: int, centre_y: int, radius: int) -> list[tuple[float, tuple[int, int, int]]]:
    """The orb's vertical ramp, sampled top to bottom.

    Black letters are drawn over the circle, so at every height the widest
    saturated pixel in a horizontal scan wins; the letters then never decide a
    colour stop.
    """
    pixels = master.convert("RGBA").load()
    stops: list[tuple[float, tuple[int, int, int]]] = []
    steps = 9
    for index in range(steps):
        fraction = index / (steps - 1)
        y = round(centre_y - radius + fraction * 2 * radius)
        best: tuple[int, tuple[int, int, int]] | None = None
        for offset in range(-radius + 2, radius - 1, 2):
            x = centre_x + offset
            if not (0 <= x < master.width and 0 <= y < master.height):
                continue
            pixel = pixels[x, y]
            if not is_brand(pixel):
                continue
            spread = max(pixel[:3]) - min(pixel[:3])
            if best is None or spread > best[0]:
                best = (spread, pixel[:3])
        if best:
            stops.append((round(fraction, 3), best[1]))
    # Collapse near-duplicate stops so the SVG does not carry noise.
    compact = [stops[0]]
    for fraction, colour in stops[1:]:
        if sum(abs(a - b) for a, b in zip(colour, compact[-1][1])) > 12:
            compact.append((fraction, colour))
    return compact


def render_orb(size: int, stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """The mark on its own: a flat vertical ramp, as the original draws it."""
    ramp = Image.new("RGBA", (1, size))
    for y in range(size):
        ramp.putpixel((0, y), (*interpolate(stops, y / size), 255))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    orb = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    orb.paste(ramp.resize((size, size), Image.BILINEAR), (0, 0), mask)
    return orb


def interpolate(stops: list[tuple[float, tuple[int, int, int]]], position: float) -> tuple[int, int, int]:
    if position <= stops[0][0]:
        return stops[0][1]
    for (start, first), (end, second) in zip(stops, stops[1:]):
        if position <= end:
            span = end - start or 1
            step = (position - start) / span
            return tuple(round(a + (b - a) * step) for a, b in zip(first, second))  # type: ignore[return-value]
    return stops[-1][1]


def orb_svg(size: int, stops: list[tuple[float, tuple[int, int, int]]]) -> str:
    ramp = "".join(
        f'<stop offset="{fraction:.3f}" stop-color="#{r:02x}{g:02x}{b:02x}"/>'
        for fraction, (r, g, b) in stops
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="RadLab">'
        f"<defs><linearGradient id=\"radlab-orb\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">{ramp}</linearGradient></defs>"
        f'<rect width="{size}" height="{size}" fill="none"/>'
        f'<circle cx="{size / 2}" cy="{size / 2}" r="{size / 2}" fill="url(#radlab-orb)"/>'
        f"</svg>\n"
    )


def og_card(logo: Image.Image, stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """Open Graph default: the wordmark on a dark field with the orb glowing."""
    canvas = Image.new("RGBA", OG_SIZE, (*APPLE_TILE, 255))
    glow = Image.new("RGBA", OG_SIZE, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((OG_SIZE[0] // 2 - 60, 90, OG_SIZE[0] // 2 + 460, 600),
                                 fill=(*interpolate(stops, 0.35), 60))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    scaled = logo.copy()
    scaled.thumbnail((OG_SIZE[0] - 320, OG_SIZE[1] - 300))
    canvas.alpha_composite(scaled, ((OG_SIZE[0] - scaled.width) // 2, (OG_SIZE[1] - scaled.height) // 2))
    return canvas.convert("RGB")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = Image.open(fetch(SOURCE, TMP / "logo.png")).convert("RGBA")
    centre_x, centre_y, radius = circle_geometry(master)
    stops = gradient_stops(master, centre_x, centre_y, radius)
    print("orb  r=" + str(radius) + "  stops: " + " ".join(f"#{r:02x}{g:02x}{b:02x}" for _, (r, g, b) in stops))

    # Header and footer: the original artwork, one variant per theme.
    master.save(OUT / "logo.png", "PNG", optimize=True)
    recolour_dark_parts(master, DARK_THEME_WORDMARK).save(OUT / "logo-inverted.png", "PNG", optimize=True)

    # The circle rebuilt from those stops: favicon, tiles, the hero orb.
    mark = render_orb(512, stops)
    mark.save(OUT / "mark.png", "PNG", optimize=True)
    mark.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png", "PNG", optimize=True)
    (OUT / "favicon.svg").write_text(orb_svg(64, stops), encoding="utf-8")

    tile = Image.new("RGB", (512, 512), APPLE_TILE)
    tile.paste(mark, (56, 56), mark)
    tile.save(OUT / "apple-touch.png", "PNG", optimize=True)

    og_card(recolour_dark_parts(master, DARK_THEME_WORDMARK), stops).save(OUT / "og-default.jpg", "JPEG", quality=86)

    for item in sorted(OUT.glob("*")):
        if item.is_file():
            print(f"  {item.name:22} {item.stat().st_size/1024:6.1f} KB")
    print(f"brand assets -> {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
