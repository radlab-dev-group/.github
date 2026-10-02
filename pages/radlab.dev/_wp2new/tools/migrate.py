"""One-off migration: WordPress -> Markdown working tree.

Reads the cached REST API payloads (see tools/wp.py) and the resolved media map
(tools/images.py) and writes editable Markdown into ``pl/blog/posts/`` and
``en/blog/posts/``.

The pairing problem is the reason this script keeps state. English posts are the
same articles but five of them were given different slugs, the English dates
drift by up to ten days, and the pre-2024 English posts are not translations at
all -- they are Polish text sitting at an English URL. So pairings are recorded
in ``data/translations.json`` and preserved across runs (never re-derived, or a
hand-correction silently disappears), and every English body is measured against
its Polish original: a near-identical body is marked untranslated and that post
becomes a draft rather than a Polish article published under /en/.

    python3 tools/migrate.py               # write posts that are missing
    python3 tools/migrate.py --dry-run     # show what would change
    python3 tools/migrate.py --report      # pairing + translation audit only
    python3 tools/migrate.py --overwrite   # rewrite even hand-edited files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import html2md
import wp

SITE_ROOT = Path(__file__).resolve().parent.parent
DATA = SITE_ROOT / "data"
MANIFEST = DATA / "media_map.json"
TRANSLATIONS = DATA / "translations.json"

# Polish function words. An "English" post still dense with these is Polish.
POLISH_MARKERS = re.compile(
    r"\b(?:się|że|w|na|z|do|dla|jest|są|jak|ale|o|przez|może|lub|ten|ta|to|który|która"
    r"|bardzo|tak|nie|tego|tej|tym|co|mamy|jest|będzie|być|mają|nasz|naszej|tego)\b",
    re.I,
)
POLISH_LETTERS = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")


@dataclass
class Post:
    lang: str
    wp_id: int
    slug: str
    title: str
    date: str            # ISO date, canonical for the pair comes from PL
    updated: str
    body_html: str
    excerpt: str
    tags: list[str]
    categories: list[str]
    featured: str | None


def load_posts(lang: str) -> list[Post]:
    terms_name = {}
    for taxonomy in ("categories", "post_tag"):
        for term in wp.terms(lang, taxonomy):
            terms_name[(taxonomy, term["id"])] = clean_term_name(term["name"])

    featured_urls = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        featured_urls = {e["post"]: e["local"] for e in manifest.values() if e.get("role") == "featured"}

    result: list[Post] = []
    for record in wp.posts(lang):
        result.append(Post(
            lang=lang,
            wp_id=record["id"],
            slug=record["slug"],
            title=strip_html(record["title"]["rendered"]),
            date=record["date"][:10],
            updated=record.get("modified", record["date"])[:10],
            body_html=record["content"]["rendered"],
            excerpt=strip_html(record.get("excerpt", {}).get("rendered", "")),
            tags=[terms_name.get(("post_tag", tid), str(tid)) for tid in record.get("tags", [])],
            categories=[terms_name.get(("categories", cid), str(cid)) for cid in record.get("categories", [])],
            featured=featured_urls.get(record["slug"]),
        ))
    return result


def clean_term_name(name: str) -> str:
    """A category is literally named "Q&amp;A" -- term names arrive escaped."""
    return strip_html(name).strip()


def strip_html(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment or "")
    text = wp_unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def wp_unescape(text: str) -> str:
    import html
    # WordPress double-escapes some term names ("Q&amp;amp;A").
    for _ in range(2):
        text = html.unescape(text)
    return text


# ---------------------------------------------------------------- translation

def normalise_for_compare(body_html: str) -> str:
    """Strip markup and whitespace so PL and EN bodies can be compared."""
    text = re.sub(r"<[^>]+>", " ", body_html)
    text = wp_unescape(text)
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def polish_ratio(text: str) -> float:
    """Share of Polish markers + diacritics per 100 words."""
    words = re.findall(r"\S+", text)
    if not words:
        return 0.0
    markers = len(POLISH_MARKERS.findall(text))
    diacritics = len(POLISH_LETTERS.findall(text))
    return (markers + diacritics) / max(1, len(words)) * 100


def prose(body_html: str) -> str:
    """Readable text only: code blocks and URLs are dropped before measuring.

    Technical posts quote Polish example sentences and link to slugs like
    /dwa-nowe-modele-encoderow-dla-polskiego/. Leaving those in pushes a
    genuinely translated post's Polish density up until it overlaps the
    untranslated ones; with them removed the two groups separate cleanly
    (translated 1.0-4.2, untranslated 6.9-68, Polish originals 45-59).
    """
    text = re.sub(r"<(pre|code)\b.*?</\1>", " ", body_html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return re.sub(r"\s+", " ", wp_unescape(text)).strip()


# Measured, not chosen: every translated post lands below 4.2 and every
# untranslated one above 6.9 once code and URLs are excluded.
POLISH_DENSITY_DRAFT_ABOVE = 5.0


def is_untranslated(pl_body: str, en_body: str) -> tuple[bool, str]:
    """A post is untranslated when its English body is the Polish body, or still
    reads Polish. Both are measured against the corpus, never assumed."""
    pl_norm = normalise_for_compare(pl_body)
    en_norm = normalise_for_compare(en_body)
    if not pl_norm or not en_norm:
        return True, "empty body"
    if pl_norm == en_norm:
        return True, "identical to Polish"
    if pl_norm[:400] == en_norm[:400]:
        return True, "first 400 chars identical"
    ratio = polish_ratio(prose(en_body))
    return ratio > POLISH_DENSITY_DRAFT_ABOVE, f"Polish density {ratio:.2f}/100 words"


def pair_candidates(pl: list[Post], en: list[Post]) -> dict[str, dict]:
    """Guess PL slug -> {"en": slug|None, "verified": bool}.

    Titles are useless here: a Polish title shares no tokens with its own
    English translation. Exact slug identity is the only self-evident signal,
    and it covers 18 of 23. The five that were renamed while being translated
    are matched on publication date -- the English install copies each post a
    day to ten days later and nothing else in the corpus is that close -- and
    flagged verified=false so a person confirms them before they publish.
    """
    by_slug = {post.slug: post for post in en}
    taken: set[str] = set()
    mapping: dict[str, dict] = {}

    for pl_post in pl:
        if pl_post.slug in by_slug:
            mapping[pl_post.slug] = {"en": pl_post.slug, "verified": True}
            taken.add(pl_post.slug)
        else:
            mapping[pl_post.slug] = {"en": None, "verified": False}

    free = [post for post in en if post.slug not in taken]
    pending = [p for p in pl if mapping[p.slug]["en"] is None]

    # Shared attachment names settle most of the renamed posts outright: the
    # English install re-uploaded the same files, and the overlap is decisive
    # (the true pair shares 7 images, the tempting wrong one shares 0).
    for pl_post in list(pending):
        scored = [(len(_image_names(pl_post) & _image_names(e)), e) for e in free]
        scored = [(count, e) for count, e in scored if count > 0]
        if not scored:
            continue
        count, best = max(scored, key=lambda pair: (pair[0], pair[1].slug))
        rivals = [e.slug for c, e in scored if c == count and e is not best]
        if rivals:  # ambiguous, do not guess silently
            continue
        mapping[pl_post.slug] = {"en": best.slug, "verified": True, "shared_images": count}
        free.remove(best)
        pending.remove(pl_post)

    # Whatever is left falls back to publication date, assigned smallest gap
    # first across all candidates. Picking per-post is wrong: two December
    # posts tie at 12 days and a per-post scan then swaps them.
    candidates = sorted(
        ((abs(_days(e.date, p.date)), p.slug, e.slug) for p in pending for e in free),
    )
    for gap, pl_slug, en_slug in candidates:
        if mapping[pl_slug]["en"] is not None or en_slug not in [f.slug for f in free]:
            continue
        if gap > 20:
            continue
        mapping[pl_slug] = {"en": en_slug, "verified": False, "date_gap_days": gap}
        free = [f for f in free if f.slug != en_slug]
    return mapping


def _image_names(post: Post) -> set[str]:
    """Bare attachment names, size suffix removed."""
    names = re.findall(r'src="(https?://[^"]+)"', post.body_html)
    cleaned = set()
    for url in names:
        name = url.split("?")[0].rsplit("/", 1)[-1].lower()
        name = re.sub(r"-\d+x\d+(?=\.\w+$)", "", name)
        cleaned.add(re.sub(r"-(?:png|jpe?g|gif|webp|avif)$", "", name.rsplit(".", 1)[0]))
    return cleaned


def _days(iso_a: str, iso_b: str) -> int:
    from datetime import date
    def parse(value: str) -> date:
        year, month, day = (int(part) for part in value[:10].split("-"))
        return date(year, month, day)
    return (parse(iso_a) - parse(iso_b)).days


def load_translations() -> dict:
    if TRANSLATIONS.exists():
        return json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    return {}


# ------------------------------------------------------------------- output

def yaml_scalar(value: str) -> str:
    """Quote only when needed, and never let a Polish title lose its letters."""
    if value is None:
        return '""'
    needs_quote = bool(re.search(r'^[\s>|&*!%@`{}\[\]"\'#-]|[:#]\s|^\s|\s$', value)) or '"' in value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"' if needs_quote or '"' not in value else f"'{value}'"


def front_matter(post: Post, *, translation_of: str | None, draft: bool, description: str) -> str:
    lines = [
        f"title: {yaml_scalar(post.title)}",
        f"date: {post.date}",
    ]
    if post.updated and post.updated != post.date:
        lines.append(f"updated: {post.updated}")
    lines.append(f"slug: {post.slug}")
    if description:
        lines.append(f"description: {yaml_scalar(description)}")
    if post.tags:
        lines.append("tags: [" + ", ".join(yaml_scalar(t) for t in post.tags) + "]")
    if post.categories:
        lines.append("categories: [" + ", ".join(yaml_scalar(c) for c in post.categories) + "]")
    if post.featured:
        lines.append(f"image: {post.featured}")
    lines.append(f"lang: {post.lang}")
    if translation_of:
        lines.append(f"translation_of: {translation_of}")
    if draft:
        lines.append("draft: true")
    lines.append(f"wp_id: {post.wp_id}")
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def media_resolver():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    lookup = {wp.fix_dead_host(url.split("?")[0]): entry
              for url, entry in manifest.items() if entry.get("role") != "featured"}

    def resolve(url: str):
        # Post bodies still carry the dead wp.radlab.dev host; the manifest is
        # keyed on the repaired URL.
        return lookup.get(wp.fix_dead_host((url or "").split("?")[0]))
    return resolve


def render(post: Post, resolve, *, translation_of: str | None, draft: bool) -> tuple[str, html2md.Report]:
    body, report = html2md.convert(post.body_html, post.slug, resolve=resolve)
    description = post.excerpt[:160].rsplit(" ", 1)[0] if post.excerpt else ""
    if description and not description.endswith("…"):
        description += "…"
    return front_matter(post, translation_of=translation_of, draft=draft,
                        description=description) + body, report


def cmd_migrate(args: argparse.Namespace) -> int:
    pl_posts = load_posts("pl")
    en_posts = load_posts("en")
    pl_by_slug = {p.slug: p for p in pl_posts}
    en_by_slug = {p.slug: p for p in en_posts}

    stored = load_translations()
    guessed = pair_candidates(pl_posts, en_posts)
    updated_map = False
    unverified: list[str] = []

    audit: list[str] = []
    resolve = media_resolver()
    written = skipped = 0

    for pl_post in sorted(pl_posts, key=lambda p: p.date):
        pair = stored.get(pl_post.slug) or guessed.get(pl_post.slug)
        if pl_post.slug not in stored:
            stored[pl_post.slug] = pair
            updated_map = True
        # Accept the older plain-string form so an existing map still loads.
        if isinstance(pair, str):
            pair = {"en": pair, "verified": True}
        en_slug = (pair or {}).get("en")
        verified = (pair or {}).get("verified", True)

        en_post = en_by_slug.get(en_slug) if en_slug else None
        if en_post:
            untranslated, reason = is_untranslated(pl_post.body_html, en_post.body_html)
        else:
            untranslated, reason = True, "no English counterpart"
        if en_slug and not verified:
            unverified.append(f"{pl_post.slug} -> {en_slug}")
        audit.append(f"{pl_post.slug[:40]:42} en={(en_slug or '—')[:50]:52} "
                     f"{'DRAFT' if untranslated else 'ok   '} "
                     f"{'' if verified else 'GUESSED-PAIR '}{reason}")

        targets = [("pl", pl_post, None, False)]
        if en_post:
            targets.append(("en", en_post, pl_post.slug, untranslated))

        for lang, post, translation_of, draft in targets:
            out = SITE_ROOT / lang / "blog" / "posts" / f"{post.slug}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists() and not args.overwrite:
                skipped += 1
                continue
            markdown, report = render(post, resolve, translation_of=translation_of, draft=draft)
            if not args.dry_run:
                out.write_text(markdown, encoding="utf-8")
            written += 1
            problems = []
            if report.images_unresolved:
                problems.append(f"{len(report.images_unresolved)} unresolved image(s)")
            if report.images_missing_alt:
                problems.append(f"{len(report.images_missing_alt)} image(s) without alt")
            if problems:
                audit.append(f"    {lang}/{post.slug}: " + "; ".join(problems))

    if updated_map and not args.dry_run:
        TRANSLATIONS.parent.mkdir(parents=True, exist_ok=True)
        TRANSLATIONS.write_text(json.dumps(dict(sorted(stored.items())), ensure_ascii=False, indent=1),
                                encoding="utf-8")

    print("\n".join(audit))
    print(f"\nwrote {written}, skipped existing {skipped}, "
          f"translations map has {len(stored)} pairs")
    if unverified:
        print(f"\n{len(unverified)} pairings were guessed from publication date and "
              f"need confirming in data/translations.json:")
        for line in unverified:
            print(f"  {line}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("--overwrite", action="store_true",
                        help="rewrite files that already exist (default: never touch them)")
    parser.add_argument("--report", action="store_true", help="audit only, write nothing")
    args = parser.parse_args(argv)
    if args.report:
        args.dry_run = True
    return cmd_migrate(args)


if __name__ == "__main__":
    raise SystemExit(main())
