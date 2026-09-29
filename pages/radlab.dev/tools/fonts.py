"""Fetch and self-host the two font families the design uses.

Nothing on the site talks to a CDN at runtime, so the WOFF2 files live in
``static/fonts/`` and are served from our own origin. Only the ``latin`` and
``latin-ext`` subsets are taken -- latin-ext is what carries ą ę ł ń ó ś ź ż,
and without it Polish text silently falls back to a different typeface mid
sentence, which on an editorial layout is visible immediately.

    python3 tools/fonts.py

The CSS already declares a full fallback stack (Georgia for the serif, system-ui
for the sans), so skipping this only costs polish, never correctness.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "fonts"

# A modern UA is required: Google Fonts serves TTF to old user agents and only
# emits WOFF2 (and the subset split) for browsers that advertise support.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

FAMILIES = {
    # Variable ranges keep this to a handful of files instead of one per weight.
    "newsreader": "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600&display=swap",
    "inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400..700&display=swap",
}
KEEP_SUBSETS = {"latin", "latin-ext"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


FACE = re.compile(r"(?:/\*\s*([\w-]+)\s*\*/\s*)?@font-face\s*\{.*?\}", re.S)


def css_blocks(css: str):
    """Yield (subset, face_css) so subsets can be filtered.

    Google Fonts marks each block with a preceding /* subset */ comment, and
    that comment is the only place the subset name appears -- so it has to be
    captured as part of the same match. Splitting on @font-face first detaches
    the comment and every block inherits the previous block's subset.
    """
    for match in FACE.finditer(css):
        yield match.group(1), match.group(0).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for family, css_url in FAMILIES.items():
        css = fetch(css_url).decode("utf-8")
        kept = 0
        for subset, block in css_blocks(css):
            if subset and subset not in KEEP_SUBSETS:
                continue
            for url in re.findall(r"url\((https://[^)]+\.woff2)\)", block):
                weight = re.search(r"font-weight:\s*([\d\s]+);", block)
                style = re.search(r"font-style:\s*(\w+);", block)
                suffix = f"-{subset}" if subset else ""
                name = (f"{family}-{(weight.group(1).strip().replace(' ', '-') if weight else '400')}"
                        f"-{style.group(1) if style else 'normal'}{suffix}.woff2")
                target = OUT / name
                target.write_bytes(fetch(url))
                kept += 1
                print(f"  {name:48} {target.stat().st_size/1024:7.1f} KB")
        print(f"{family}: {kept} files")
        written += kept
    total = sum(f.stat().st_size for f in OUT.glob("*.woff2"))
    print(f"\n{written} font files, {total/1024:.0f} KB total in {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
