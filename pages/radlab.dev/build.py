#!/usr/bin/env python3
"""Static site builder for radlab.dev -- a landing page plus a bilingual blog.

Content lives in ``pl/`` and ``en/`` as Markdown. Posts are ``<lang>/blog/posts/*.md``
with YAML front matter; the landing page is a set of section files
``<lang>/home/*.md`` sorted by their ``order`` key, so adding a section is adding a
file and nothing needs to be registered anywhere.

URLs follow the legacy WordPress layout on purpose (``/2025-10-13/llm-router/``)
so six years of inbound links keep working without a redirect map. English sits
under ``/en/``; the two are tied together with hreflang through
``data/translations.json``, because five English posts were given different
slugs when they were translated and no string comparison can recover that.

    python3 build.py                 # build dist/
    python3 build.py --serve         # build, then serve on :8010 and rebuild on change
    python3 build.py --check         # build, then fail on broken links or assets
    python3 build.py --fast          # skip image variants (preview builds)
    python3 build.py --verbose       # show individual content, images and output files
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import mimetypes
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

try:  # Python 3.11 has tomllib; 3.10 needs tomli.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

import markdown as markdown_lib
from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound

MEDIA_TOKEN = "@media"
MEDIA_DIR = ROOT / "media"
BUILD_STATE = ".build-state.json"


MONTHS = {
    "pl": ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
           "lipca", "sierpnia", "września", "października", "listopada", "grudnia"],
    # English month names would read wrong for a date written 14 December,
    # so the ISO form stays where no localisation helps the reader.
    "en": None,
}


def format_date(value, lang: str = "pl") -> str:
    """Long Polish date (14 grudnia 2025), ISO for other languages.

    Accepts date, datetime or ISO string because front matter yields whichever
    PyYAML happened to infer.
    """
    if isinstance(value, str):
        try:
            value = dt.date.fromisoformat(value[:10])
        except ValueError:
            return str(value)
    if isinstance(value, dt.datetime):
        value = value.date()
    names = MONTHS.get(lang)
    if not names:
        return value.isoformat()
    return f"{value.day} {names[value.month - 1]} {value.year}"


# --------------------------------------------------------------------- config

@dataclass
class Config:
    raw: dict
    root: Path = ROOT

    @property
    def site(self) -> dict:
        return self.raw["site"]

    @property
    def url(self) -> str:
        return self.site.get("url", "").rstrip("/")

    @property
    def base(self) -> str:
        base = self.site.get("base_path", "")
        return "" if base in ("", "/") else "/" + base.strip("/")

    @property
    def langs(self) -> list[str]:
        return self.site["langs"]

    @property
    def default_lang(self) -> str:
        return self.site["default_lang"]

    @property
    def image_widths(self) -> list[int]:
        return self.raw.get("images", {}).get("widths", [480, 768, 1024, 1440])

    @property
    def per_page(self) -> int:
        return self.raw.get("blog", {}).get("per_page", 8)

    @property
    def blog_path(self) -> str:
        return self.raw.get("blog", {}).get("path", "blog")

    def prefix(self, lang: str) -> str:
        """Path prefix for a language: PL at the root, EN under /en/."""
        return f"{self.base}/{lang}" if lang != self.default_lang else self.base

    def href(self, lang: str, path: str) -> str:
        """Absolute-from-server path for a language, with a trailing slash.

        Every internal link goes through here. Relative links would break the
        moment the same page is reachable from two directory depths, which is
        exactly what a date-based URL scheme gives you.
        """
        # Every page URL is a directory URL and carries the trailing slash; the
        # old WordPress permalinks did too, and mixing the two forms splits the
        # same page across two addresses.
        cleaned = path.strip("/")
        joined = f"{self.prefix(lang)}/{cleaned}" if cleaned else f"{self.prefix(lang)}/"
        joined = re.sub(r"(?<!:)/{2,}", "/", joined)
        return joined if joined.endswith("/") else joined + "/"

    def canonical(self, lang: str, path: str) -> str:
        return self.url + self.href(lang, path)


def load_config(path: Path) -> Config:
    with path.open("rb") as handle:
        return Config(tomllib.load(handle))


# ----------------------------------------------------------------- documents

class FrontMatter(dict):
    """Front matter as a plain mapping; a dict subclass rather than a dataclass
    so unknown keys survive without having to be declared anywhere."""


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split ``---\\nyaml---\\nbody``. Hand-rolled to keep PyYAML the only dep."""
    match = re.match(r"\A---[ \t]*\r?\n(.*?)(?:\r?\n)---[ \t]*\r?\n?", text, re.S)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data, text[match.end():]


@dataclass
class Post:
    lang: str
    meta: FrontMatter
    body_markdown: str
    html: str = ""
    url_path: str = ""

    @property
    def slug(self) -> str:
        return self.meta.get("slug", "")

    @property
    def date(self) -> dt.date:
        value = self.meta.get("date")
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            return value
        if isinstance(value, dt.datetime):
            return value.date()
        return dt.date.fromisoformat(str(value)[:10])

    @property
    def title(self) -> str:
        return self.meta.get("title", self.slug)

    @property
    def description(self) -> str:
        return self.meta.get("description", "")

    @property
    def draft(self) -> bool:
        return bool(self.meta.get("draft", False))

    @property
    def tags(self) -> list[str]:
        return list(self.meta.get("tags") or [])

    @property
    def image(self) -> str | None:
        return self.meta.get("image")

    @property
    def path(self) -> str:
        """Legacy WordPress layout: /YYYY-MM-DD/slug/"""
        return f"{self.date.isoformat()}/{self.slug}"

    @property
    def reading_minutes(self) -> int:
        words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", self.html)))
        return max(1, round(words / 200))


@dataclass
class Product:
    lang: str
    meta: FrontMatter
    body_markdown: str
    html: str = ""
    url_path: str = ""

    @property
    def slug(self) -> str:
        return self.meta.get("slug", "")

    @property
    def title(self) -> str:
        return self.meta.get("title", self.slug)

    @property
    def subtitle(self) -> str:
        return self.meta.get("subtitle", "")

    @property
    def description(self) -> str:
        return self.meta.get("description", "")

    @property
    def icon(self) -> str:
        return self.meta.get("icon", "router")

    @property
    def tags(self) -> list[str]:
        return list(self.meta.get("tags") or [])

    @property
    def actions(self) -> list[dict]:
        return list(self.meta.get("actions") or [])

    @property
    def path(self) -> str:
        return f"products/{self.slug}"


def load_products(cfg: Config, lang: str) -> list[Product]:
    directory = ROOT / lang / "products"
    if not directory.exists():
        return []
    products: list[Product] = []
    for path in sorted(directory.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        if not meta.get("slug"):
            meta["slug"] = path.stem
        prod = Product(lang=lang, meta=FrontMatter(meta), body_markdown=body)
        prod.url_path = cfg.href(lang, prod.path)
        products.append(prod)
    return products


def load_posts(cfg: Config, lang: str, *, include_drafts: bool) -> list[Post]:
    directory = ROOT / lang / "blog" / "posts"
    posts: list[Post] = []
    for path in sorted(directory.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        meta.setdefault("slug", path.stem)
        post = Post(lang=lang, meta=FrontMatter(meta), body_markdown=body)
        if post.draft and not include_drafts:
            continue
        posts.append(post)
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def load_sections(cfg: Config, lang: str) -> list[dict]:
    """Landing page sections, ordered by their front matter `order` key."""
    directory = ROOT / lang / "home"
    sections = []
    for path in sorted(directory.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        meta["_file"] = path.name
        meta.setdefault("order", 100)
        meta["_html"] = render_markdown(body, cfg)
        sections.append(meta)
    sections.sort(key=lambda s: (s.get("order", 100), s["_file"]))
    return sections


def load_ui(cfg: Config, lang: str) -> dict:
    path = ROOT / lang / "ui.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_translations() -> dict[str, dict]:
    path = ROOT / "data" / "translations.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Tolerate the plain "pl slug": "en slug" shape from earlier migrations.
    return {k: (v if isinstance(v, dict) else {"en": v, "verified": True}) for k, v in raw.items()}


# ------------------------------------------------------------- markdown

SHORTCODE_YOUTUBE = re.compile(r"\{\{<\s*youtube\s+([\w-]{11})\s*>}}")
SHORTCODE_VIDEO = re.compile(r"\{\{<\s*video\s+(https?://\S+?)\s*>}}")
SHORTCODE_DETAILS = re.compile(r"\{\{<\s*details\s+title=\"([^\"]*)\"\s*>}}(.*?)\{\{<\s*/details\s*>}}", re.S)
SHORTCODE_CALLOUT = re.compile(r"\{\{<\s*callout\s*>}}(.*?)\{\{<\s*/callout\s*>}}", re.S)

MARKDOWN_EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.fenced_code",
    "markdown.extensions.codehilite",
    "markdown.extensions.attr_list",
    "markdown.extensions.sane_lists",
    "markdown.extensions.toc",
]


def render_markdown(text: str, cfg: Config) -> str:
    text = expand_shortcodes(text)
    engine = markdown_lib.Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs={
            "markdown.extensions.codehilite": {
                "css_class": "codehilite",
                "guess_lang": False,
                "noclasses": False,
                "pygments_style": "default",
            },
            "markdown.extensions.toc": {"permalink": " "},
        },
        output_format="html5",
    )
    body = engine.convert(text)
    return body


def article_outline(body: str) -> list[dict]:
    class OutlineParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.entries = []
            self.heading = None

        def handle_starttag(self, tag, attrs):
            if tag in ("h2", "h3"):
                anchor = dict(attrs).get("id")
                self.heading = {"id": anchor, "level": tag, "text": ""} if anchor else None

        def handle_data(self, data):
            if self.heading is not None:
                self.heading["text"] += data

        def handle_endtag(self, tag):
            if self.heading is not None and tag == self.heading["level"]:
                self.heading["text"] = " ".join(self.heading["text"].split())
                if self.heading["text"]:
                    self.entries.append(self.heading)
                self.heading = None

    parser = OutlineParser()
    parser.feed(body)
    return parser.entries


def expand_shortcodes(text: str) -> str:
    """The three constructs WordPress had that Markdown has no equivalent for."""

    def youtube(match: re.Match[str]) -> str:
        video_id = match.group(1)
        return (
            f'<div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/{video_id}" '
            f'title="YouTube" loading="lazy" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            f'allowfullscreen></iframe></div>'
        )

    def details(match: re.Match[str]) -> str:
        title, inner = html.escape(match.group(1)), match.group(2).strip()
        rendered = markdown_lib.markdown(inner, extensions=["fenced_code", "tables"])
        return f"<details><summary>{title}</summary><div>{rendered}</div></details>"

    def callout(match: re.Match[str]) -> str:
        inner = markdown_lib.markdown(match.group(1).strip(), extensions=["fenced_code"])
        return f'<aside class="callout">{inner}</aside>'

    def video(match: re.Match[str]) -> str:
        # The .webm files stay on the origin rather than being mirrored --
        # 64 MB of video for five posts is not worth the repository -- so they
        # load lazily and never block the page.
        url = html.escape(match.group(1).strip(), quote=True)
        return (f'<div class="embed embed-video"><video controls preload="none" '
                f'src="{url}"></video></div>')

    text = SHORTCODE_YOUTUBE.sub(youtube, text)
    text = SHORTCODE_VIDEO.sub(video, text)
    text = SHORTCODE_DETAILS.sub(details, text)
    text = SHORTCODE_CALLOUT.sub(callout, text)
    return text


# ------------------------------------------------------------- images

class BuildProgress:
    def __init__(self, *, verbose: bool = False):
        self.verbose = verbose

    def stage(self, step: int, message: str) -> None:
        print(f"[{step}/5] {message}", flush=True)

    def detail(self, message: str) -> None:
        if self.verbose:
            print(f"  {message}", flush=True)


class ImagePipeline:
    """Turns ``![](@media/slug/file.png)`` into a <picture> with WebP srcset.

    Sources are the archived originals; variants are generated once into
    ``dist/assets/img/`` and keyed by a content hash so an unchanged picture is
    never re-encoded and a changed one never serves a stale variant.
    """

    def __init__(self, cfg: Config, dist: Path, *, enabled: bool = True,
                 progress: BuildProgress | None = None):
        self.cfg = cfg
        self.dist = dist
        self.enabled = enabled
        self.progress = progress if progress is not None else BuildProgress()
        self.out_dir = dist / "assets" / "img"
        self.manifest = self._load_manifest()
        self.cache: dict[tuple[str, int], dict | None] = {}
        self.missing: list[str] = []
        try:  # Pillow is optional so a text-only build still works without it.
            from PIL import Image  # noqa: F401
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass
            self.available = enabled
        except ModuleNotFoundError:
            self.available = False

    @staticmethod
    def _load_manifest() -> dict:
        path = ROOT / "data" / "media_map.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def master_for(self, token_path: str) -> Path | None:
        """Resolve ``@media/slug/file`` to a decoded master on disk."""
        relative = token_path[len(MEDIA_TOKEN):].lstrip("/") if token_path.startswith(MEDIA_TOKEN) else token_path
        for entry in self.manifest.values():
            if entry["local"] == f"media/{relative}" or entry["local"].endswith(f"/{Path(relative).name}") \
                    and entry["post"] == Path(relative).parent.name:
                master = entry.get("master")
                candidate = ROOT / master if master else ROOT / entry["local"]
                if candidate.exists():
                    return candidate
        direct = MEDIA_DIR / relative
        return direct if direct.exists() else None

    def variants(self, source: Path) -> dict | None:
        if not self.enabled or not self.available:
            return None
        if source in self.cache:
            return self.cache[source]

        from PIL import Image, UnidentifiedImageError

        self.progress.detail(f"Processing image: {source}")
        try:
            with Image.open(source) as image:
                image.load()
                width, height = image.size
                digest = hashlib.sha1(source.read_bytes()).hexdigest()[:10]
                result: dict = {"width": width, "height": height, "webp": {}, "original": None}

                self.out_dir.mkdir(parents=True, exist_ok=True)
                target_widths = [w for w in self.cfg.image_widths if w <= width] or [width]
                for target in target_widths:
                    out = self.out_dir / f"{digest}-{target}.webp"
                    if not out.exists():
                        self.progress.detail(f"Generating WebP: {out.name} ({target}px)")
                        resized = image.copy()
                        if target != width:
                            resized = image.resize((target, round(height * target / width)), Image.LANCZOS)
                        resized.save(out, "WEBP", quality=82, method=4)
                    else:
                        self.progress.detail(f"Reusing WebP: {out.name} ({target}px)")
                    result["webp"][target] = f"/assets/img/{out.name}"

                fallback = self.out_dir / f"{digest}{source.suffix.lower()}"
                if not fallback.exists():
                    shutil.copyfile(source, fallback)
                result["original"] = f"/assets/img/{fallback.name}"
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            self.missing.append(f"{source}: {exc}")
            self.progress.detail(f"Image failed: {source}: {exc}")
            result = None

        self.cache[source] = result
        return result

    def picture_html(self, token_path: str, alt: str, css_class: str = "",
                     sizes: str | None = None) -> str:
        source = self.master_for(token_path)
        if source is None:
            self.missing.append(f"unresolved image: {token_path}")
            return f'<img src="{html.escape(token_path)}" alt="{html.escape(alt)}">'

        data = self.variants(source)
        if data is None:  # images disabled or Pillow unavailable: plain tag
            path = self.cfg.base + "/media/" + token_path[len(MEDIA_TOKEN):].lstrip("/")
            return f'<img src="{html.escape(path)}" alt="{html.escape(alt)}" loading="lazy">'

        srcset = ", ".join(f"{self.cfg.base}{url} {w}w" for w, url in sorted(data["webp"].items()))
        # The default is the article column; a thumbnail in a card would pay for
        # a 720px decode without it, so the caller who knows the box says so.
        sizes = sizes or "(max-width: 760px) 100vw, 720px"
        fallback = self.cfg.base + data["original"]
        classes = f' class="{css_class}"' if css_class else ""
        # width/height are mandatory: they reserve the box so the layout does
        # not jump when a lazy image finally arrives.
        return (
            f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img src="{html.escape(fallback)}" alt="{html.escape(alt)}"'
            f' width="{data["width"]}" height="{data["height"]}"'
            f' loading="lazy" decoding="async"{classes}></picture>'
        )

    def og_image(self, post: Post) -> str | None:
        """OG images must be PNG or JPEG -- social crawlers do not fetch WebP."""
        if not post.image or not self.available:
            return None
        source = self.master_for(post.image.replace("media/", f"{MEDIA_TOKEN}/"))
        if source is None:
            source = ROOT / post.image
        if not source.exists():
            return None
        from PIL import Image

        out = self.dist / "assets" / "og"
        out.mkdir(parents=True, exist_ok=True)
        target = out / f"{post.lang}-{post.slug}.jpg"
        if not target.exists():
            self.progress.detail(f"Generating OG image: {target.name}")
            try:
                with Image.open(source) as image:
                    image.load()
                    canvas = Image.new("RGB", (1200, 630), (255, 255, 255))
                    scaled = image.copy()
                    scaled.thumbnail((1200, 630))
                    canvas.paste(scaled, ((1200 - scaled.width) // 2, (630 - scaled.height) // 2))
                    canvas.save(target, "JPEG", quality=82)
            except OSError:
                return None
        else:
            self.progress.detail(f"Reusing OG image: {target.name}")
        return f"{self.cfg.base}/assets/og/{target.name}"


def apply_images(body: str, pipeline: ImagePipeline) -> str:
    """Rewrite every ``@media`` reference in rendered HTML to a <picture>.

    Done on the output HTML rather than in Markdown so an image inside a
    shortcode, a raw HTML block or a figure caption takes exactly the same path.
    """

    def replace_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        src = re.search(r'src="([^"]*)"', tag)
        if not src or not src.group(1).startswith(MEDIA_TOKEN):
            return tag
        alt = re.search(r'alt="([^"]*)"', tag)
        return pipeline.picture_html(src.group(1), alt.group(1) if alt else "")

    # <img src> inside <source srcset> is not a thing here; only img tags.
    return re.sub(r"<img\b[^>]*>", replace_img, body)


# ------------------------------------------------------------------ builder

class Site:
    def __init__(self, cfg: Config, *, fast: bool = False, include_drafts: bool = False,
                 verbose: bool = False):
        self.cfg = cfg
        self.include_drafts = include_drafts
        self.dist = ROOT / "dist"
        self.progress = BuildProgress(verbose=verbose)
        self.pipeline = ImagePipeline(cfg, self.dist, enabled=not fast, progress=self.progress)
        self.env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.globals["cfg"] = cfg
        self.env.filters["datefmt"] = format_date
        self.posts: dict[str, list[Post]] = {}
        self.drafts: dict[str, list[Post]] = {}
        self.products: dict[str, list[Product]] = {}
        self.sections: dict[str, list[dict]] = {}
        self.ui: dict[str, dict] = {}
        self.translations = load_translations()
        self.problems: list[str] = []

    # -- data

    def load(self) -> None:
        for lang in self.cfg.langs:
            every = load_posts(self.cfg, lang, include_drafts=True)
            self.drafts[lang] = [p for p in every if p.draft]
            self.posts[lang] = [p for p in every if not p.draft] if not self.include_drafts else every
            self.products[lang] = load_products(self.cfg, lang)
            self.sections[lang] = load_sections(self.cfg, lang)
            self.ui[lang] = load_ui(self.cfg, lang)
        self.env.globals["ui"] = self.ui

    def originals_of(self, draft: Post) -> Post | None:
        """For an untranslated English draft: the Polish post it stands for."""
        if draft.lang == self.cfg.default_lang:
            return None
        for pl_slug, pair in self.translations.items():
            if pair.get("en") == draft.slug:
                return next((p for p in self.posts[self.cfg.default_lang] if p.slug == pl_slug), None)
        return next((p for p in self.posts[self.cfg.default_lang] if p.slug == draft.slug), None)

    def cards(self, lang: str) -> list[dict]:
        """Everything the blog index shows.

        Untranslated English posts are drafts and publish nowhere, but hiding
        them outright would make the English blog look twice as short as the
        Polish one. They appear as entries pointing at the Polish original,
        labelled as missing, which is honest and keeps the two lists the same
        length.
        """
        entries = [{"post": post, "missing": None} for post in self.posts[lang]]
        if lang != self.cfg.default_lang:
            for draft in self.drafts[lang]:
                original = self.originals_of(draft)
                if original is None:
                    continue
                entries.append({"post": draft, "missing": original})
        entries.sort(key=lambda card: card["post"].date, reverse=True)
        return entries

    def counterpart(self, post: Post) -> Post | None:
        """The same article in the other language, or None."""
        other = "en" if post.lang == self.cfg.default_lang else self.cfg.default_lang
        if other == "en":
            pair = self.translations.get(post.slug) or {}
            target = pair.get("en")
        else:
            target = next((pl for pl, pair in self.translations.items()
                           if pair.get("en") == post.slug), None)
        if not target:
            return None
        return next((p for p in self.posts.get(other, []) if p.slug == target), None)

    def alternates(self, *, path: str, lang: str, counterpart_path: str | None) -> list[tuple[str, str]]:
        """hreflang pairs. A lone self-referencing alternate is pointless, so a
        document with no counterpart emits nothing."""
        pairs: list[tuple[str, str]] = []
        if counterpart_path:
            other = "en" if lang == self.cfg.default_lang else self.cfg.default_lang
            pairs = [(self.cfg.site["hreflang"][lang], self.cfg.canonical(lang, path)),
                     (self.cfg.site["hreflang"][other], self.cfg.canonical(other, counterpart_path)),
                     ("x-default", self.cfg.canonical(self.cfg.default_lang, path))]
        return pairs

    # -- rendering

    def render_post_html(self, post: Post) -> str:
        return apply_images(render_markdown(post.body_markdown, self.cfg), self.pipeline)

    def image(self, src: str, alt: str = "", css_class: str = "", sizes: str | None = None) -> Markup:
        """A <picture> from a template, for anything outside a post body.

        Front matter writes `image: media/slug/file.png` while the pipeline
        speaks `@media/slug/file.png`; both spellings are accepted here so the
        template never has to know which one a field holds.
        """
        token = src if src.startswith(MEDIA_TOKEN) else src.replace("media/", f"{MEDIA_TOKEN}/", 1)
        return Markup(self.pipeline.picture_html(token, alt, css_class, sizes))

    def brand_image(self, name: str) -> str | None:
        """A brand asset URL, or None when tools/brand.py has not been run."""
        path = ROOT / "static" / "img" / name
        return f"{self.cfg.base}/assets/img/{name}" if path.exists() else None

    def context(self, lang: str, *, switch_href: str | None = None) -> dict:
        return {
            "lang": lang,
            "ui": self.ui[lang],
            "site": self.cfg.site,
            "href": lambda path, current=lang: self.cfg.href(current, path),
            "switch_href": switch_href if switch_href is not None else self.other_index(lang),
            "base": self.cfg.base,
            "posts": self.posts[lang],
            "image": self.image,
            "logo": self.brand_image("logo.png"),
            "logo_inverted": self.brand_image("logo-inverted.png"),
            "og_default": self.brand_image("og-default.jpg"),
        }

    def other_index(self, lang: str) -> str:
        """Fallback for the language switch: the other language's landing page."""
        return self.cfg.href("en" if lang == self.cfg.default_lang else self.cfg.default_lang, "")

    def switch_url(self, current: str, target: str | None) -> str:
        """Language switcher target: the same article in the other language, and
        when it is not translated, the other language's blog index -- never a
        dead link."""
        other = "en" if current == self.cfg.default_lang else self.cfg.default_lang
        if target:
            return self.cfg.href(other, target)
        return self.cfg.href(other, self.cfg.blog_path)

    # -- outputs

    def build(self) -> None:
        self.progress.stage(1, "Loading content and configuration...")
        self.dist.mkdir(parents=True, exist_ok=True)
        self.load()
        image_mode = "responsive images enabled" if self.pipeline.available else "image generation disabled"
        self.progress.stage(2, f"Rendering Markdown ({image_mode})...")
        for lang in self.cfg.langs:
            for post in self.posts[lang]:
                self.progress.detail(f"Rendering post: {lang}/{post.path}")
                post.html = self.render_post_html(post)
            for product in self.products[lang]:
                self.progress.detail(f"Rendering product: {lang}/{product.path}")
                product.html = apply_images(render_markdown(product.body_markdown, self.cfg), self.pipeline)
        self.progress.stage(3, "Copying static assets and writing syntax highlighting CSS...")
        self.write_static()
        self.write_pygments_css()
        self.progress.stage(4, "Generating HTML pages and social preview images...")
        for lang in self.cfg.langs:
            self.build_home(lang)
            self.build_blog_index(lang)
            for product in self.products[lang]:
                self.build_product(product)
            for post in self.posts[lang]:
                self.build_post(post)
        self.progress.stage(5, "Generating feeds, sitemap and auxiliary files...")
        self.build_feeds()
        self.build_sitemap()
        self.build_misc()

    def write(self, path: str, content: str) -> None:
        # A directory URL ("/", "/blog/") is written as its index file.
        if path in ("", "/"):
            path = "index.html"
        elif path.endswith("/"):
            path += "index.html"
        target = self.dist / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.progress.detail(f"Wrote: {path}")

    def build_home(self, lang: str) -> None:
        template = self.env.get_template("home.html")
        ctx = self.context(lang, switch_href=self.other_index(lang))
        ctx["sections"] = self.sections[lang]
        # One post leads the blog block with its picture, the rest sit beside it.
        ctx["latest"] = self.posts[lang][:4]
        ctx["page_title"] = self.cfg.site["name"]
        ctx["canonical"] = self.cfg.canonical(lang, "")
        ctx["alternates"] = self.home_alternates(lang)
        self.write(self.strip(self.cfg.href(lang, "")), template.render(**ctx))

    def home_alternates(self, lang: str) -> list[tuple[str, str]]:
        return [(self.cfg.site["hreflang"][code], self.cfg.canonical(code, ""))
                for code in self.cfg.langs]

    def build_blog_index(self, lang: str) -> None:
        template = self.env.get_template("blog_list.html")
        cards = self.cards(lang)
        per_page = self.cfg.per_page
        pages = [cards[i:i + per_page] for i in range(0, len(cards), per_page)] or [[]]
        for index, group in enumerate(pages, start=1):
            path = "blog" if index == 1 else f"blog/page/{index}"
            other = "en" if lang == self.cfg.default_lang else self.cfg.default_lang
            ctx = self.context(lang, switch_href=self.cfg.href(other, path))
            ctx.update({
                "page_posts": group,
                "default_lang": self.cfg.default_lang,
                "page_number": index,
                "page_count": len(pages),
                "page_title": self.ui[lang].get("blog_title", "Blog"),
                "canonical": self.cfg.canonical(lang, path),
                "prev_url": self.cfg.href(lang, "blog" if index == 2 else f"blog/page/{index-1}"),
                "next_url": self.cfg.href(lang, f"blog/page/{index+1}"),
                "alternates": [],
            })
            self.write(self.strip(self.cfg.href(lang, path)), template.render(**ctx))

    def build_post(self, post: Post) -> None:
        template = self.env.get_template("post.html")
        mate = self.counterpart(post)
        ctx = self.context(post.lang, switch_href=self.switch_url(post.lang, mate.path if mate else None))
        ctx.update({
            "post": post,
            "content": post.html,
            "outline": article_outline(post.html),
            "page_title": post.title,
            "page_description": post.description,
            "canonical": self.cfg.canonical(post.lang, post.path),
            "og_image": self.pipeline.og_image(post),
            "counterpart": mate,
            "alternates": self.alternates(path=post.path, lang=post.lang,
                                          counterpart_path=mate.path if mate else None),
        })
        self.write(self.strip(self.cfg.href(post.lang, post.path)), template.render(**ctx))

    def build_product(self, product: Product) -> None:
        template = self.env.get_template("product.html")
        other = "en" if product.lang == self.cfg.default_lang else self.cfg.default_lang
        mate = next((p for p in self.products.get(other, []) if p.slug == product.slug), None)
        ctx = self.context(product.lang, switch_href=self.cfg.href(other, mate.path) if mate else self.other_index(product.lang))
        ctx.update({
            "product": product,
            "content": product.html,
            "page_title": product.title,
            "page_description": product.description,
            "canonical": self.cfg.canonical(product.lang, product.path),
            "counterpart": mate,
            "alternates": self.alternates(path=product.path, lang=product.lang,
                                          counterpart_path=mate.path if mate else None),
        })
        self.write(self.strip(self.cfg.href(product.lang, product.path)), template.render(**ctx))

    def build_feeds(self) -> None:
        template = self.env.get_template("feed.xml")
        for lang in self.cfg.langs:
            ctx = self.context(lang)
            ctx["posts"] = self.posts[lang][:20]
            ctx["feed_url"] = self.cfg.canonical(lang, "feed.xml")
            ctx["site_url"] = self.cfg.canonical(lang, "")
            self.write(self.strip(f"{self.cfg.prefix(lang)}/feed.xml"), template.render(**ctx))

    def build_sitemap(self) -> None:
        template = self.env.get_template("sitemap.xml")
        entries = []
        for lang in self.cfg.langs:
            entries.append({"loc": self.cfg.canonical(lang, ""),
                            "alternates": self.home_alternates(lang),
                            "lastmod": None})
            entries.append({"loc": self.cfg.canonical(lang, "blog"), "alternates": [],
                            "lastmod": None})
            other = "en" if lang == self.cfg.default_lang else self.cfg.default_lang
            for product in self.products[lang]:
                mate = next((p for p in self.products.get(other, []) if p.slug == product.slug), None)
                entries.append({
                    "loc": self.cfg.canonical(lang, product.path),
                    "alternates": self.alternates(path=product.path, lang=lang,
                                                  counterpart_path=mate.path if mate else None),
                    "lastmod": None,
                })
            for post in self.posts[lang]:
                mate = self.counterpart(post)
                entries.append({
                    "loc": self.cfg.canonical(lang, post.path),
                    "alternates": self.alternates(path=post.path, lang=lang,
                                                  counterpart_path=mate.path if mate else None),
                    "lastmod": (post.meta.get("updated") or post.date),
                })
        self.write("sitemap.xml", template.render(entries=entries))

    def build_misc(self) -> None:
        (self.dist / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\nSitemap: {self.cfg.url}/sitemap.xml\n", encoding="utf-8")
        self.progress.detail("Wrote: robots.txt")
        template = self.env.get_template("404.html")
        self.write("404.html", template.render(**self.context(self.cfg.default_lang)))

    def write_static(self) -> None:
        target = self.dist / "assets"
        for folder in ("css", "js", "fonts", "img"):
            source = ROOT / "static" / folder
            if not source.is_dir():
                continue
            for item in source.rglob("*"):
                if item.is_file():
                    destination = target / item.relative_to(ROOT / "static")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(item, destination)
                    self.progress.detail(f"Copied: {destination.relative_to(self.dist)}")

    def write_pygments_css(self) -> None:
        """Code colours come from CSS custom properties rather than two
        stylesheets, so highlighting follows the theme with no extra request."""
        target = self.dist / "assets" / "css"
        target.mkdir(parents=True, exist_ok=True)
        (target / "highlight.css").write_text(HIGHLIGHT_CSS, encoding="utf-8")
        self.progress.detail("Wrote: assets/css/highlight.css")

    @staticmethod
    def strip(path: str) -> str:
        return path.lstrip("/")


HIGHLIGHT_CSS = """/* Token colours are variables so one stylesheet serves light and dark. */
.codehilite, .highlight { background: var(--code-bg); border-radius: 8px; }
.codehilite { overflow-x: auto; font-size: .875rem; line-height: 1.55; padding: 1rem 1.15rem; }
.codehilite code { font-family: var(--font-mono); }
.codehilite .k, .codehilite .kd, .codehilite .kn, .codehilite .kr, .codehilite .kt { color: var(--tok-keyword); }
.codehilite .nf, .codehilite .nc, .codehilite .nd { color: var(--tok-name); }
.codehilite .s, .codehilite .s1, .codehilite .s2, .codehilite .sb, .codehilite .se { color: var(--tok-string); }
.codehilite .mi, .codehilite .mf, .codehilite .m, .codehilite .mh { color: var(--tok-number); }
.codehilite .c, .codehilite .c1, .codehilite .cm, .codehilite .cs { color: var(--tok-comment); font-style: italic; }
.codehilite .o, .codehilite .ow, .codehilite .p { color: var(--tok-punct); }
.codehilite .nb, .codehilite .bp { color: var(--tok-builtin); }
.codehilite .nt, .codehilite .na, .codehilite .nv { color: var(--tok-tag); }
"""


# ------------------------------------------------------------------ checks

def check_links(dist: Path, cfg: Config) -> list[str]:
    """Every internal href and img src in dist/ must resolve to a built file."""
    problems: list[str] = []
    pages = list(dist.rglob("*.html"))
    known: set[str] = set()
    for path in dist.rglob("*"):
        if path.is_file():
            relative = "/" + str(path.relative_to(dist))
            known.add(relative)
            if relative.endswith("/index.html"):
                known.add(relative[: -len("index.html")])

    base = cfg.base
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r'(?:href|src|content)="(/[^"#]*?)"', text):
            value = match.group(1)
            if value.startswith("//") or value.startswith(base + "/youtube"):
                continue
            cleaned = value.split("?")[0]
            if cleaned in known:
                continue
            if (dist / cleaned.lstrip("/")).exists():
                continue
            if re.search(r"\.(css|js|xml|txt|jpg|jpeg|png|webp|avif|svg|woff2?)$", cleaned):
                problems.append(f"{page.relative_to(dist)}: missing asset {value}")
            elif not cleaned.endswith((".html", "/")):
                problems.append(f"{page.relative_to(dist)}: broken link {value}")
            else:
                problems.append(f"{page.relative_to(dist)}: broken link {value}")
    return problems


def check_no_media_token(dist: Path) -> list[str]:
    """A surviving @media token or {{< shortcode >}} means the pipeline missed
    something: both are syntax the migration emits and only the builder expands."""
    problems = []
    for page in dist.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        # Strip the inline theme script, whose closing `})();` looks like one.
        body = re.sub(r"<script>.*?</script>", "", text, flags=re.S)
        if "@media/" in body:
            problems.append(f"{page.relative_to(dist)}: unresolved @media reference")
        leaked = re.findall(r"\{\{<[^>]*>}}", body)
        if leaked:
            problems.append(f"{page.relative_to(dist)}: unexpanded shortcode {leaked[:2]}")
    return problems


# ---------------------------------------------------------------- serve

def serve(dist: Path, port: int, base: str = "") -> None:
    import http.server
    import socketserver

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dist), **kwargs)

        def guess_type(self, path):
            if str(path).endswith(".svg"):
                return "image/svg+xml"
            if str(path).endswith(".woff2"):
                return "font/woff2"
            return super().guess_type(path)

        def log_message(self, *args):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with Server(("127.0.0.1", port), Handler) as httpd:
        print(f"serving {dist} on http://127.0.0.1:{port}{base}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


# ------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=ROOT / "site.toml")
    parser.add_argument("--serve", action="store_true", help="serve dist/ after building")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--check", action="store_true", help="verify links and assets, non-zero exit on failure")
    parser.add_argument("--drafts", action="store_true", help="include draft posts (unpublished)")
    parser.add_argument("--fast", action="store_true", help="skip image generation")
    parser.add_argument("-v", "--verbose", action="store_true", help="show detailed build progress")
    parser.add_argument("--base-path", help="override site.base_path (for a subpath preview)")
    parser.add_argument("--clean", action="store_true", help="remove dist/ first")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    if args.base_path is not None:
        cfg.raw["site"]["base_path"] = args.base_path

    if args.clean and (ROOT / "dist").exists():
        shutil.rmtree(ROOT / "dist")

    site = Site(cfg, fast=args.fast, include_drafts=args.drafts, verbose=args.verbose)
    site.build()

    built = len(list((ROOT / "dist").rglob("*.html")))
    print(f"built {built} pages -> dist/  "
          f"({sum(len(v) for v in site.posts.values())} posts, "
          f"{'fast/no images' if args.fast else f'{len(site.pipeline.cache)} image sources'})")
    if site.pipeline.missing:
        print(f"  {len(site.pipeline.missing)} image problem(s):", file=sys.stderr)
        for line in site.pipeline.missing[:10]:
            print(f"    {line}", file=sys.stderr)

    if args.check:
        print("Checking internal links and assets...", flush=True)
        problems = check_links(ROOT / "dist", cfg) + check_no_media_token(ROOT / "dist")
        if problems:
            print(f"\n{len(problems)} problem(s):", file=sys.stderr)
            for line in problems[:40]:
                print(f"  {line}", file=sys.stderr)
            return 1
        print("check: all internal links and assets resolve")

    if args.serve:
        serve(ROOT / "dist", args.port, cfg.base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
