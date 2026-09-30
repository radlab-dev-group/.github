"""Resolve the images used by the blog to their full-resolution originals and
download them into ``media/<slug>/``.

The rendered post HTML points at whatever the webp-uploads plugin decided to
serve that day: a downscaled ``-1024x796.avif``, an ``image-1-png.avif`` whose
PNG original still exists two URLs away, or a dead ``wp.radlab.dev`` host left
behind by a bad search-replace. Downloading what ``src`` says would bake those
soft derivatives in permanently, so every image is resolved through the media
API back to its ``source_url`` first, and only falls back to the derivative
when no original can be found (recorded as a warning in the manifest).

    python3 tools/images.py                   # download what is missing
    python3 tools/images.py --report          # what resolved where, and what did not
    python3 tools/images.py hotlinks --lang en  # archive leftover absolute URLs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import wp

SITE_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = SITE_ROOT / "media"
MANIFEST = SITE_ROOT / "data" / "media_map.json"

UA = "radlab-dev-migration (read-only content export)"
SIZE_SUFFIX = re.compile(r"-\d+x\d+(?=\.[A-Za-z0-9]+$)")
IMG_TAG = re.compile(r"<img\b[^>]*?>", re.I)
SRC_ATTR = re.compile(r'src="([^"]+)"', re.I)

# WordPress re-encodes uploads to avif/webp and mangles the stem while doing it
# ("image-1.png" -> "image-1-png.avif"). Candidates are tried in order.
CANDIDATE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif")


def url_dirname(url: str) -> str:
    return urllib.parse.urlparse(url).path.rsplit("/", 1)[0]


def url_filename(url: str) -> str:
    return urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])


def stem_of(filename: str) -> str:
    """Base name without extension and without a -WxH derivative suffix."""
    base = SIZE_SUFFIX.sub("", filename)
    root = base.rsplit(".", 1)[0]
    # webp-uploads renames "foo.png" to "foo-png.webp"; drop that trailing tag.
    return re.sub(r"-(png|jpe?g|gif|webp|avif)$", "", root, flags=re.I)


class MediaIndex:
    """Lookup of attachment records by directory + stem, built from the API."""

    def __init__(self, records: list[dict]):
        self.by_dir_stem: dict[tuple[str, str], dict] = {}
        self.by_exact: dict[str, dict] = {}
        for record in records:
            source = record.get("source_url")
            if not source:
                continue
            self.by_exact.setdefault(source, record)
            name = url_filename(source)
            self.by_dir_stem.setdefault((url_dirname(source), stem_of(name)), record)
            # Derivative sizes also map back to their parent attachment.
            for size in (record.get("media_details") or {}).get("sizes", {}).values():
                for key in ("file", "source_url"):
                    value = size.get(key)
                    if isinstance(value, str):
                        self.by_exact.setdefault(_join(source, value), record)

    def resolve(self, image_url: str) -> dict | None:
        url = wp.fix_dead_host(image_url)
        if url in self.by_exact:
            return self.by_exact[url]
        path = urllib.parse.urlparse(url).path
        # Derivatives live in the same directory as the original.
        record = self.by_dir_stem.get((url_dirname(url), stem_of(url_filename(url))))
        if record:
            return record
        # Last resort: same directory, try plausible original names.
        for ext in CANDIDATE_EXTS:
            guess = f"{url.rstrip('/')}"
            root = guess.rsplit(".", 1)[0]
            candidate = SIZE_SUFFIX.sub("", root) + ext
            if candidate != guess:
                return {"guessed_url": candidate}
        return None


def _join(source_url: str, relative_file: str) -> str:
    """media_details sizes give a bare filename or a path relative to uploads/."""
    if relative_file.startswith("http"):
        return relative_file
    base = urllib.parse.urlparse(source_url)
    directory = urllib.parse.unquote(base.path).rsplit("/", 1)[0]
    directory = re.sub(r"/[^/]+\.\w+$", "", directory)
    return f"{base.scheme}://{base.netloc}{directory}/{urllib.parse.quote(relative_file)}"


def post_image_urls(lang: str) -> dict[str, list[str]]:
    """slug -> ordered unique image URLs used by that post."""
    result: dict[str, list[str]] = {}
    for post in wp.posts(lang):
        urls: list[str] = []
        for tag in IMG_TAG.findall(post["content"]["rendered"]):
            src = SRC_ATTR.search(tag)
            # Keep the URL exactly as authored: the dead-host count depends on
            # seeing it before the rewrite. Resolution applies the fix.
            if src and src.group(1).startswith("http") and src.group(1) not in urls:
                urls.append(src.group(1))
        result[post["slug"]] = urls
    return result


def download(url: str, dest: Path) -> tuple[bool, int, str]:
    if dest.exists() and dest.stat().st_size > 0:
        return True, dest.stat().st_size, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, 0, f"FAILED {exc}"
    if not payload:
        return False, 0, "FAILED empty response"
    dest.write_bytes(payload)
    return True, len(payload), "downloaded"


def featured_images(lang: str) -> dict[str, str]:
    """slug -> featured image URL.

    Every post has a featured image but most do not show it in the body, so it
    never appears in post_image_urls(); the blog cards and OG tags need it.
    """
    by_id = {record.get("id"): record for record in wp.media(lang)}
    result: dict[str, str] = {}
    for post in wp.posts(lang):
        record = by_id.get(post.get("featured_media"))
        url = (record or {}).get("source_url")
        if url:
            result[post["slug"]] = wp.fix_dead_host(url)
    return result


def build(lang: str = "pl", *, dry_run: bool = False) -> dict:
    index = MediaIndex(wp.media(lang))
    manifest: dict[str, dict] = {}
    used_by_slug = post_image_urls(lang)

    for slug, urls in sorted(used_by_slug.items()):
        for position, served in enumerate(urls, start=1):
            url = wp.fix_dead_host(served)
            record = index.resolve(url)
            original = (record or {}).get("source_url") or (record or {}).get("guessed_url") or url
            name = url_filename(original)
            stem = stem_of(name) or "image"
            ext = url_filename(original).rsplit(".", 1)[-1].lower()
            local_rel = f"media/{slug}/{position:02d}-{stem}.{ext}"

            entry = {
                "post": slug,
                "served_url": url,          # what the old HTML pointed at
                "original_url": original,   # what we actually archive
                "local": local_rel,
                "resolved_via_api": bool(record and record.get("source_url")),
                "host_was_dead": wp.is_dead_host(served),
            }
            if not dry_run:
                ok, size, note = download(original, SITE_ROOT / local_rel)
                entry.update(bytes=size, status=note)
                if not ok:  # fall back to the derivative rather than lose the image
                    entry["fallback_of"] = original
                    ok2, size2, note2 = download(url, SITE_ROOT / local_rel)
                    entry.update(bytes=size2, status=note2 if ok2 else f"{note} / then {note2}")
                    entry["used_derivative"] = ok2
            manifest[url] = entry

    for slug, url in sorted(featured_images(lang).items()):
        ext = url_filename(url).rsplit(".", 1)[-1].lower()
        local_rel = f"media/{slug}/_featured.{ext}"
        entry = {"post": slug, "original_url": url, "local": local_rel,
                 "resolved_via_api": True, "host_was_dead": False, "role": "featured"}
        if not dry_run:
            ok, size, note = download(url, SITE_ROOT / local_rel)
            entry.update(bytes=size, status=note)
        manifest[f"featured:{slug}"] = entry
    return manifest


def find_master(url: str) -> str | None:
    """A Pillow-readable original for an asset the build cannot decode.

    Pillow on this machine has no AVIF support at all -- it cannot even open
    ``.avif`` -- while 39 of the archived images are AVIF because the webp-uploads
    plugin replaced the attachment. Most of those still have their PNG original
    sitting at a guessable sibling URL, which is both higher quality and
    readable; the remainder are decoded through ImageMagick, which does carry a
    libavif delegate.
    """
    base = re.sub(r"\.(avif|heic|heif)$", "", url, flags=re.I)
    if base == url:
        return None  # not an AVIF; already usable
    for ext in (".png", ".jpg", ".jpeg"):
        candidate = base + ext
        try:
            request = urllib.request.Request(candidate, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status == 200 and int(response.headers.get("Content-Length") or 0) > 0:
                    return candidate
        except (urllib.error.URLError, TimeoutError):
            continue
    return None


def decode_with_imagemagick(src: Path, dest: Path) -> bool:
    """Fallback decode for an AVIF with no PNG original. ImageMagick is probed,
    never assumed: a build must not depend on a delegate that may be absent."""
    binary = next((b for b in ("/usr/bin/convert", "/usr/bin/magick") if Path(b).exists()), None)
    if binary is None:
        return False
    import subprocess
    try:
        subprocess.run([binary, str(src), str(dest)], check=True, capture_output=True, timeout=120)
    except (subprocess.SubprocessError, OSError):
        return False
    return dest.exists() and dest.stat().st_size > 0


def upgrade_masters(dry_run: bool = False) -> dict:
    """Give every asset a master the build can read, recorded as entry['master']."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    stats = {"already": 0, "original_found": 0, "decoded": 0, "unusable": 0}

    for key, entry in manifest.items():
        local = SITE_ROOT / entry["local"]
        extension = local.suffix.lower()
        if extension not in (".avif", ".heic", ".heif"):
            entry["master"] = entry["local"]
            stats["already"] += 1
            continue

        master_rel = entry["local"].rsplit(".", 1)[0] + ".png"
        master = SITE_ROOT / master_rel
        original = find_master(entry["original_url"])
        if original:
            target = master.with_suffix(Path(urllib.parse.urlparse(original).path).suffix.lower())
            target_rel = str(target.relative_to(SITE_ROOT))
            if not dry_run:
                ok, size, note = download(original, target)
                if not ok:
                    stats["unusable"] += 1
                    continue
                entry["master"] = target_rel
                entry["master_bytes"] = size
            else:
                entry["master"] = target_rel
            stats["original_found"] += 1
        elif not dry_run and decode_with_imagemagick(local, master):
            entry["master"] = master_rel
            entry["master_bytes"] = master.stat().st_size
            stats["decoded"] += 1
        else:
            entry["unusable"] = True
            stats["unusable"] += 1

    if not dry_run:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return stats


def cmd_upgrade(args: argparse.Namespace) -> int:
    stats = upgrade_masters(dry_run=args.dry_run)
    print("masters: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
    if stats["unusable"]:
        print(f"  {stats['unusable']} asset(s) have no decodable source; they will be "
              f"linked as-is with no responsive variants", file=sys.stderr)
    return 0


MD_IMAGE = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif")


def archive_hotlinks(lang: str, *, dry_run: bool = False) -> dict:
    """Move images a post still hotlinks into ``media/`` and rewrite the link.

    The translated posts came over with their own WordPress host in the body:
    the Polish articles reference ``@media/`` tokens, the English ones point at
    ``https://en.radlab.dev/...``, so those pages render only for as long as the
    legacy site answers. Same manifest shape as build(), same decodable-master
    lookup as upgrade(). Links that are not images -- a PDF report, a screen
    recording -- are left alone: the media pipeline has nothing to add to them.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    stats = {"rewritten": 0, "kept": 0, "failed": 0, "posts": 0}

    for path in sorted((SITE_ROOT / lang / "blog" / "posts").glob("*.md")):
        slug = path.stem
        text = original_text = path.read_text(encoding="utf-8")
        touched = False
        # Continue the numbering of anything already local in this post.
        position = max([int(n) for n in re.findall(rf"@media/{slug}/(\d+)-", text)] or [0])
        for alt, url in MD_IMAGE.findall(text):
            if not url.lower().rsplit("?", 1)[0].endswith(IMAGE_EXT):
                stats["kept"] += 1
                continue
            position += 1
            name = url_filename(urllib.parse.urlparse(url).path)
            stem = stem_of(name) or "image"
            ext = name.rsplit(".", 1)[-1].lower()
            local_rel = f"media/{slug}/{position:02d}-{stem}.{ext}"
            token = f"@media/{slug}/{position:02d}-{stem}.{ext}"

            if dry_run:
                stats["rewritten"] += 1
                touched = True
                continue

            ok, size, note = download(url, SITE_ROOT / local_rel)
            if not ok:
                stats["failed"] += 1
                print(f"  FAILED {slug}: {url} ({note})", file=sys.stderr)
                continue

            entry = {"post": slug, "served_url": url, "original_url": url, "local": local_rel,
                     "resolved_via_api": False, "host_was_dead": False,
                     "bytes": size, "status": note}
            if ext in ("avif", "heic", "heif"):
                master_url = find_master(url)
                master_rel = f"media/{slug}/{position:02d}-{stem}.png"
                if master_url:
                    sibling_ext = master_url.rsplit(".", 1)[-1].lower()
                    master_rel = master_rel.rsplit(".", 1)[0] + f".{sibling_ext}"
                    ok_master, master_size, _ = download(master_url, SITE_ROOT / master_rel)
                    entry["master"] = master_rel if ok_master else local_rel
                    entry["master_bytes"] = master_size if ok_master else 0
                elif decode_with_imagemagick(SITE_ROOT / local_rel, SITE_ROOT / master_rel):
                    entry["master"] = master_rel
                    entry["master_bytes"] = (SITE_ROOT / master_rel).stat().st_size
                else:
                    entry["master"] = local_rel  # linked as-is, no variants
            else:
                entry["master"] = local_rel

            manifest[url] = entry
            text = text.replace(f"]({url})", f"]({token})")
            stats["rewritten"] += 1

        if touched or text != original_text:
            stats["posts"] += 1
            if not dry_run:
                path.write_text(text, encoding="utf-8")

    if not dry_run and stats["rewritten"]:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return stats


def cmd_hotlinks(args: argparse.Namespace) -> int:
    stats = archive_hotlinks(args.lang, dry_run=args.dry_run)
    print(f"hotlinks[{args.lang}]: {stats['rewritten']} image(s) archived across "
          f"{stats['posts']} post(s), {stats['kept']} non-image link(s) left alone, "
          f"{stats['failed']} failed"
          + ("   [dry run, nothing written]" if args.dry_run else ""))
    return 1 if stats["failed"] else 0


def cmd_run(args: argparse.Namespace) -> int:
    manifest = build(args.lang, dry_run=args.dry_run)
    if not args.dry_run:
        # Merging matters: a bilingual site runs this once per language, and the
        # second run must not erase the first language's mappings.
        existing = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
        existing.update(manifest)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(existing, ensure_ascii=False, indent=1), encoding="utf-8")

    body = {u: e for u, e in manifest.items() if e.get("role") != "featured"}
    featured = {u: e for u, e in manifest.items() if e.get("role") == "featured"}
    total = len(body)
    via_api = sum(1 for e in manifest.values() if e["resolved_via_api"])
    dead = sum(1 for e in manifest.values() if e["host_was_dead"])
    failed = [u for u, e in manifest.items() if e.get("status", "").startswith("FAILED")]
    derivative = [u for u, e in manifest.items() if e.get("used_derivative")]
    size = sum(e.get("bytes", 0) for e in manifest.values())

    print(f"images: {total} unique body images + {len(featured)} featured, "
          f"{via_api} resolved to an API original, "
          f"{dead} recovered from the dead wp.radlab.dev host")
    print(f"        {size/1024/1024:.1f} MB on disk, {len(failed)} failed")
    if derivative:
        print(f"        {len(derivative)} fell back to a served derivative (softer than the original)")
    if args.report:
        grouped: dict[str, list[str]] = defaultdict(list)
        for url, entry in manifest.items():
            grouped[entry["post"]].append(
                f"    {entry['local']}  <- {entry.get('served_url') or entry['original_url']}"
                + ("" if entry["resolved_via_api"] else "   [NOT in media API]")
                + ("" if not entry.get("status") else f"   [{entry['status']}]"))
        for slug in sorted(grouped):
            print(f"\n{slug}")
            print("\n".join(grouped[slug]))
    for url in failed:
        print(f"  FAILED: {url}", file=sys.stderr)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="run", choices=("run", "upgrade", "hotlinks"),
                        help="run: download the images; upgrade: give every AVIF a "
                             "master the build can decode; hotlinks: archive the "
                             "absolute image URLs a language still points at")
    parser.add_argument("--lang", default="pl", choices=sorted(wp.ORIGINS))
    parser.add_argument("--report", action="store_true", help="print the full source -> local mapping")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = parser.parse_args(argv)
    if args.command == "upgrade":
        return cmd_upgrade(args)
    if args.command == "hotlinks":
        return cmd_hotlinks(args)
    return cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
