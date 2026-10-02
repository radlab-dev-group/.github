"""One-time relocation of the archived blog files; builds never download media."""

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "data/media_map.json").read_text(encoding="utf-8"))
masters = {entry["local"]: entry.get("master", entry["local"]) for entry in manifest.values()}
sources = sorted((ROOT / "pl/blog/posts").glob("*.md")) + sorted((ROOT / "en/blog/posts").glob("*.md"))
plans = []
videos = {}
preserved = set()

for source in sources:
    text = source.read_text(encoding="utf-8")
    destination = source.parent / source.stem
    assert not destination.exists(), destination
    references = set(re.findall(r"@?media/[^\s)\"<>]+", text))
    replacements = {}
    files = {}
    names = {}
    for reference in sorted(references):
        relative = reference.lstrip("@")
        original = ROOT / relative
        assert original.is_file(), original
        resolved = ROOT / masters.get(relative, relative)
        assert resolved.is_file(), resolved
        for item in sorted(original.parent.iterdir()):
            if item.is_file():
                name = item.name
                target = destination / "media" / name
                if target in files and files[target].read_bytes() != item.read_bytes():
                    name = item.parent.name + "-" + item.name
                    target = destination / "media" / name
                files[target] = item
                names[item] = name
                preserved.add(item)
        replacements[reference] = "media/" + names[resolved]
    for reference in re.findall(r"\{\{<\s*video\s+(https?://\S+)\s*>}}", text):
        normalized = reference.replace("https://en.radlab.dev/", "https://radlab.dev/")
        name = unquote(Path(urlsplit(reference).path).name)
        replacements[reference] = "media/" + name
        videos.setdefault(normalized, []).append(destination / "media" / name)
    for old in sorted(replacements, key=len, reverse=True):
        text = text.replace(old, replacements[old])
    plans.append((source, destination, text, files))

originals = {path for path in (ROOT / "media").rglob("*") if path.is_file()}
assert preserved == originals, f"Unassigned files: {originals - preserved}"
print(f"Posts: {len(plans)}; original files: {len(originals)}; videos: {len(videos)}", flush=True)

for source, destination, text, files in plans:
    (destination / "media").mkdir(parents=True)
    for target, original in files.items():
        shutil.copyfile(original, target)
        assert hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()
    (destination / "index.md").write_text(text, encoding="utf-8")

for url, targets in videos.items():
    print(f"Archiving video: {url}", flush=True)
    subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "2",
                    "--max-time", "120", "--output", str(targets[0]), url], check=True)
    assert targets[0].stat().st_size > 0
    subprocess.run(["file", str(targets[0])], check=True)
    for target in targets[1:]:
        shutil.copyfile(targets[0], target)

for source, destination, text, files in plans:
    for reference in re.findall(r"media/[^\s)\"<>]+", text):
        assert (destination / reference).is_file(), (destination, reference)

for source, destination, text, files in plans:
    source.unlink()
shutil.rmtree(ROOT / "media")
(ROOT / "data/media_map.json").unlink()
print("Migration complete; all archived originals preserved next to posts.", flush=True)