"""Read-only client for the RadLab WordPress REST API, with an on-disk cache.

Two installs hold the content:

    pl  https://radlab.dev      -- canonical, source of dates and slugs
    en  https://en.radlab.dev   -- translations (some still Polish)

Every request is served from ``data/wp_cache/<lang>/`` when present, so the
migration can be re-run offline and restarted without touching the network.
The API is unauthenticated; we never send anything but GET requests.

Usage:
    python3 tools/wp.py fetch            # populate the cache for both languages
    python3 tools/wp.py stats            # what is in the cache right now
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterator

SITE_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = SITE_ROOT / "data" / "wp_cache"

ORIGINS = {"pl": "https://radlab.dev", "en": "https://en.radlab.dev"}

# The legacy site has a second hostname baked into some post bodies by a bad
# search-replace; those URLs are dead and must be rewritten during migration.
DEAD_HOST = "wp.radlab.dev"

USER_AGENT = "radlab-dev-migration (read-only content export)"

POST_FIELDS = "id,slug,date,modified,link,title,content,excerpt,categories,tags,featured_media,author"
PAGE_FIELDS = "id,slug,link,parent,title,content"
MEDIA_FIELDS = "id,slug,source_url,mime_type,media_details,alt_text,title"


class WpError(RuntimeError):
    pass


def _cache_path(lang: str, name: str) -> Path:
    return CACHE_DIR / lang / name


def _get_json(url: str, *, refresh: bool = False, cache_name: str | None = None,
              lang: str | None = None) -> tuple[Any, dict[str, str]]:
    """Fetch JSON, preferring the cache. Returns (payload, response headers).

    Headers are empty on a cache hit, so callers must not rely on them there.
    """
    if lang and cache_name:
        path = _cache_path(lang, cache_name)
        if path.exists() and not refresh:
            cached = json.loads(path.read_text(encoding="utf-8"))
            # A cached error object must not be trusted as data; re-fetch instead.
            if not (isinstance(cached, dict) and cached.get("code")):
                return cached, {}

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = {k.lower(): v for k, v in response.headers.items()}

    if lang and cache_name:
        path = _cache_path(lang, cache_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload, headers


def _meta_path(lang: str, stem: str) -> Path:
    return _cache_path(lang, f"{stem}.meta.json")


def _write_meta(lang: str, stem: str, total: int, total_pages: int) -> None:
    path = _meta_path(lang, stem)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"total": total, "total_pages": total_pages}), encoding="utf-8")


def _read_meta(lang: str, stem: str, default: int = 1) -> int:
    """Page count recorded on the download that filled the cache."""
    path = _meta_path(lang, stem)
    if not path.exists():
        return default
    try:
        return max(1, int(json.loads(path.read_text(encoding="utf-8"))["total_pages"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return default


def _paged(origin: str, endpoint: str, params: dict[str, str], *, lang: str,
           cache_stem: str, refresh: bool = False, per_page: int = 100) -> Iterator[dict]:
    """Walk a paginated collection, caching each page as its own file.

    Page count comes from the X-WP-TotalPages header, never from the length of a
    page: this server returns 79 items for per_page=100 (some attachments are
    hidden from the REST response), so a "short page means last page" test would
    silently drop the remaining 84 attachments.
    """
    page = 1
    total_pages = 1
    seen_ids: set[int] = set()
    while page <= total_pages:
        query = dict(params, per_page=str(per_page), page=str(page))
        url = f"{origin}/wp-json/wp/v2/{endpoint}?{urllib.parse.urlencode(query)}"
        cache_name = f"{cache_stem}_p{page}.json"
        batch, headers = _get_json(url, lang=lang, cache_name=cache_name, refresh=refresh)
        if isinstance(batch, dict):  # WP returns an error object, not a list
            raise WpError(f"{url} -> {batch.get('code')}: {batch.get('message')}")

        if page == 1:
            reported = headers.get("x-wp-totalpages")
            if reported and reported.isdigit():
                total_pages = int(reported)
                _write_meta(lang, cache_stem, int(headers.get("x-wp-total") or 0), total_pages)
            else:
                # Cache hit: reuse the page count recorded when it was downloaded.
                total_pages = _read_meta(lang, cache_stem)
        elif not batch:
            break

        for item in batch:
            key = item.get("id")
            if isinstance(key, int):
                if key in seen_ids:
                    continue
                seen_ids.add(key)
            yield item
        page += 1
        time.sleep(0.2)  # be polite to a shared host


def posts(lang: str, *, refresh: bool = False) -> list[dict]:
    return list(_paged(ORIGINS[lang], "posts", {"_fields": POST_FIELDS},
                       lang=lang, cache_stem="posts", refresh=refresh))


def pages(lang: str, *, refresh: bool = False) -> list[dict]:
    return list(_paged(ORIGINS[lang], "pages", {"_fields": PAGE_FIELDS},
                       lang=lang, cache_stem="pages", refresh=refresh))


def media(lang: str, *, refresh: bool = False) -> list[dict]:
    return list(_paged(ORIGINS[lang], "media", {"_fields": MEDIA_FIELDS},
                       lang=lang, cache_stem="media", refresh=refresh))


# The REST route for a taxonomy is not always its PHP name: post tags live at
# /wp/v2/tags while remaining "post_tag" inside a post object.
TAXONOMY_ROUTES = {"categories": "categories", "post_tag": "tags"}


def terms(lang: str, taxonomy: str, *, refresh: bool = False) -> list[dict]:
    endpoint = TAXONOMY_ROUTES.get(taxonomy, taxonomy)
    return list(_paged(ORIGINS[lang], endpoint, {"_fields": "id,slug,name,count,parent"},
                       lang=lang, cache_stem=taxonomy, refresh=refresh))


def users(lang: str, *, refresh: bool = False) -> list[dict]:
    payload, _ = _get_json(f"{ORIGINS[lang]}/wp-json/wp/v2/users?per_page=100",
                           lang=lang, cache_name="users.json", refresh=refresh)
    return payload


LIVE_HOST = "radlab.dev"


def is_dead_host(url: str) -> bool:
    """True for the URLs a bad search-replace left pointing at a dead host."""
    return f"//{DEAD_HOST}/" in url


def fix_dead_host(url: str) -> str:
    """Rewrite //wp.radlab.dev/... to the host that actually serves the file."""
    return url.replace(f"//{DEAD_HOST}/", f"//{LIVE_HOST}/")


def cmd_fetch(args: argparse.Namespace) -> int:
    for lang in args.langs:
        print(f"[{lang}] {ORIGINS[lang]}")
        for name, fn in (
            ("posts", posts),
            ("pages", pages),
            ("categories", lambda l, refresh=False: terms(l, "categories", refresh=refresh)),
            ("post_tag", lambda l, refresh=False: terms(l, "post_tag", refresh=refresh)),
            ("users", users),
            ("media", media),
        ):
            try:
                items = fn(lang, refresh=args.refresh)
            except (WpError, urllib.error.URLError) as exc:
                print(f"  {name:12} FAILED: {exc}", file=sys.stderr)
                continue
            print(f"  {name:12} {len(items)}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    for lang in args.langs:
        directory = CACHE_DIR / lang
        if not directory.is_dir():
            print(f"[{lang}] cache empty")
            continue
        total = 0
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            count = len(data) if isinstance(data, list) else 1
            total += count
            print(f"[{lang}] {path.stem:16} {count}")
        print(f"[{lang}] --- {total} records cached")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("fetch", "stats"))
    parser.add_argument("--lang", dest="langs", nargs="+", choices=sorted(ORIGINS),
                        default=sorted(ORIGINS))
    parser.add_argument("--refresh", action="store_true",
                        help="re-download even if the cache already holds this resource")
    args = parser.parse_args(argv)
    return {"fetch": cmd_fetch, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
