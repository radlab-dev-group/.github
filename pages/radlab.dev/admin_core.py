"""Core logic for the radlab.dev blog admin panel (see ``admin.py``).

Kept free of tkinter so the same code can be exercised from the unit tests
and, one day, from a CLI. It talks to two things:

* the content tree (``content/<lang>/blog/posts/<slug>/index.md``) and
  ``config/translations.json`` — the exact layout ``build.py`` consumes;
* the LLM router through ``llm_router_lib.LLMRouterClient``. Translation uses
  ``client.translate`` for the English → Polish direction; the router's
  builtin translate endpoint is hardwired to translate *to Polish*, so the
  Polish → English direction goes through
  ``client.extended_conversation_with_model`` with an explicit
  translate-to-English system prompt instead.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent

# Mirrors [site] langs / default_lang in config/site.toml; kept as constants
# so the panel does not need a TOML parser (Python 3.10 has no tomllib).
LANGS: tuple[str, ...] = ("pl", "en")
DEFAULT_LANG = "pl"

FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)(?:\r?\n)---[ \t]*\r?\n?", re.S)

# Key order for written front matter, matching the existing posts; anything
# not listed here (e.g. wp_id) is appended in whatever order it had.
META_KEY_ORDER = (
    "title", "date", "updated", "slug", "description",
    "tags", "categories", "image", "lang", "translation_of", "draft",
)

ProgressFn = Callable[[int, int, str], None]


class PostError(Exception):
    """Base class for admin panel content errors."""


class PostNotFound(PostError):
    pass


class PostExists(PostError):
    pass


# --------------------------------------------------------------------- utils

# ą ć ę ó ś ź ż decompose under NFKD; ł and ń do not, so map them explicitly.
POLISH_SLUG_MAP = str.maketrans("łńŁŃ", "lnln")


def slugify(text: str) -> str:
    """Turn a title into a WordPress-style slug (diacritics dropped)."""
    text = text.translate(POLISH_SLUG_MAP)
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "wpis"


def unique_slug(store: "ContentStore", lang: str, base: str) -> str:
    """``base`` if free, otherwise ``base-2``, ``base-3``, ..."""
    if not store.post_exists(lang, base):
        return base
    number = 2
    while True:
        candidate = f"{base}-{number}"
        if not store.post_exists(lang, candidate):
            return candidate
        number += 1


def today_iso() -> str:
    return dt.date.today().isoformat()


PLAIN_SAFE_RE = re.compile(r"[A-Za-z0-9._/@-]+")
PLAIN_RESERVED = {"true", "false", "null", "yes", "no", "on", "off"}


def _yaml_scalar(value: str) -> str:
    """Plain scalar when it cannot be misread by YAML, quoted otherwise —
    matches the style of the checked-in posts (slugs unquoted, titles quoted)."""
    if (PLAIN_SAFE_RE.fullmatch(value) and value.lower() not in PLAIN_RESERVED
            and not value.isdigit()):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split ``---\\nyaml---\\nbody`` (same contract as build.py)."""
    import yaml
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data, text[match.end():]


def meta_to_front_matter(meta: "OrderedDict[str, object]") -> str:
    """Serialize front matter in the hand-written style the posts use."""
    lines = ["---"]
    ordered = [key for key in META_KEY_ORDER if key in meta]
    ordered += [key for key in meta if key not in META_KEY_ORDER]
    for key in ordered:
        value = meta[key]
        if key in ("tags", "categories"):
            items = ", ".join(_yaml_scalar(str(item)) for item in (value or []))
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, dt.datetime):
            lines.append(f"{key}: {value.date().isoformat()}")
        elif isinstance(value, dt.date):
            lines.append(f"{key}: {value.isoformat()}")
        else:
            lines.append(f"{key}: {_yaml_scalar(str(value))}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------- content store

@dataclass
class PostInfo:
    lang: str
    slug: str
    title: str = ""
    date: str = ""
    draft: bool = False
    counterpart: Optional[str] = None  # slug of the other-language version


@dataclass
class LoadedPost:
    lang: str
    slug: str
    meta: "OrderedDict[str, object]"
    body: str
    path: Path


class ContentStore:
    """Read/write access to ``content/<lang>/blog/posts`` + translations.json."""

    def __init__(self, root: Path | str = ROOT):
        self.root = Path(root)

    # -- paths

    def posts_dir(self, lang: str) -> Path:
        return self.root / "content" / lang / "blog" / "posts"

    def post_dir(self, lang: str, slug: str) -> Path:
        return self.posts_dir(lang) / slug

    @property
    def translations_path(self) -> Path:
        return self.root / "config" / "translations.json"

    def langs(self) -> tuple[str, ...]:
        return LANGS

    # -- listing

    def post_exists(self, lang: str, slug: str) -> bool:
        return (self.post_dir(lang, slug) / "index.md").is_file()

    def list_posts(self, lang: str | None = None) -> list[PostInfo]:
        translations = self.read_translations()
        posts: list[PostInfo] = []
        for current_lang in self.langs() if lang is None else (lang,):
            directory = self.posts_dir(current_lang)
            if not directory.is_dir():
                continue
            for index in sorted(directory.glob("*/index.md")):
                try:
                    meta, _ = parse_front_matter(index.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                slug = str(meta.get("slug") or index.parent.name)
                date_value = meta.get("date")
                if isinstance(date_value, dt.datetime):
                    date_value = date_value.date()
                if isinstance(date_value, dt.date):
                    date_iso = date_value.isoformat()
                else:
                    date_iso = str(date_value or "")[:10]
                posts.append(PostInfo(
                    lang=current_lang,
                    slug=slug,
                    title=str(meta.get("title") or slug),
                    date=date_iso,
                    draft=bool(meta.get("draft", False)),
                    counterpart=self.find_counterpart(current_lang, slug, translations),
                ))
        posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
        return posts

    def find_counterpart(self, lang: str, slug: str,
                         translations: Optional[dict] = None) -> Optional[str]:
        """Slug of the same article in the other language, or None."""
        translations = self.read_translations() if translations is None else translations
        if lang == DEFAULT_LANG:
            pair = translations.get(slug) or {}
            return pair.get("en") or None
        return next((pl for pl, pair in translations.items()
                     if (pair or {}).get("en") == slug), None)

    # -- single post

    def load_post(self, lang: str, slug: str) -> LoadedPost:
        path = self.post_dir(lang, slug) / "index.md"
        if not path.is_file():
            raise PostNotFound(f"no post {lang}/{slug}")
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        meta.setdefault("slug", slug)
        return LoadedPost(lang=lang, slug=slug, meta=OrderedDict(meta),
                          body=body, path=path)

    def save_post(self, lang: str, slug: str, meta: "OrderedDict[str, object]",
                  body: str) -> Path:
        if not slug:
            raise PostError("slug is empty")
        slug = slug.strip().lower()
        path = self.post_dir(lang, slug) / "index.md"
        meta = OrderedDict(meta)
        meta["lang"] = lang
        meta["slug"] = slug
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(meta_to_front_matter(meta) + body, encoding="utf-8")
        return path

    def delete_post(self, lang: str, slug: str) -> None:
        directory = self.post_dir(lang, slug)
        if not (directory / "index.md").is_file():
            raise PostNotFound(f"no post {lang}/{slug}")
        shutil.rmtree(directory)
        self._unlink_translation(lang, slug)

    def rename_post(self, store_lang: str, old_slug: str, new_slug: str) -> Path:
        """Move a post to a new slug and keep translations.json in sync."""
        if old_slug == new_slug:
            return self.post_dir(store_lang, old_slug) / "index.md"
        if not self.post_exists(store_lang, old_slug):
            raise PostNotFound(f"no post {store_lang}/{old_slug}")
        if self.post_exists(store_lang, new_slug):
            raise PostExists(f"post {store_lang}/{new_slug} already exists")
        source = self.post_dir(store_lang, old_slug)
        target = self.post_dir(store_lang, new_slug)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        self._relink_translation(store_lang, old_slug, new_slug)
        if store_lang == DEFAULT_LANG:
            self._sync_translation_of(old_slug, new_slug)
        return target / "index.md"

    # -- translations.json

    def read_translations(self) -> dict[str, dict]:
        path = self.translations_path
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
        # Tolerate the plain "pl slug": "en slug" shape from earlier migrations.
        return {k: (v if isinstance(v, dict) else {"en": v, "verified": True})
                for k, v in raw.items()}

    def write_translations(self, data: dict[str, dict]) -> None:
        # Exact formatting of the checked-in file: indent=1, sorted keys,
        # no trailing newline — keeps git diffs minimal.
        text = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True)
        self.translations_path.parent.mkdir(parents=True, exist_ok=True)
        self.translations_path.write_text(text, encoding="utf-8")

    def link_translation(self, pl_slug: str, en_slug: str, verified: bool = False) -> None:
        data = self.read_translations()
        entry = dict(data.get(pl_slug) or {})
        if entry.get("en") != en_slug:
            entry["en"] = en_slug
            entry["verified"] = verified
        # Keep the usual key order (en, verified, shared_images) while
        # tolerating unknown keys.
        ordered: "OrderedDict[str, object]" = OrderedDict()
        for key in ("en", "verified", "shared_images"):
            if key in entry:
                ordered[key] = entry[key]
        for key in entry:
            if key not in ordered:
                ordered[key] = entry[key]
        data[pl_slug] = ordered
        self.write_translations(data)

    def _unlink_translation(self, lang: str, slug: str) -> None:
        data = self.read_translations()
        changed = False
        if lang == DEFAULT_LANG:
            changed = data.pop(slug, None) is not None
        else:
            for key in [k for k, v in data.items() if (v or {}).get("en") == slug]:
                del data[key]
                changed = True
        if changed:
            self.write_translations(data)

    def _sync_translation_of(self, old_pl_slug: str, new_pl_slug: str) -> None:
        """Point the English post's translation_of field at the new PL slug."""
        translations = self.read_translations()
        en_slug = (translations.get(new_pl_slug) or {}).get("en")
        if not en_slug or not self.post_exists("en", en_slug):
            return
        path = self.post_dir("en", en_slug) / "index.md"
        text = path.read_text(encoding="utf-8")
        replaced = text.replace(
            f"translation_of: {old_pl_slug}", f"translation_of: {new_pl_slug}", 1)
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")

    def _relink_translation(self, lang: str, old_slug: str, new_slug: str) -> None:
        data = self.read_translations()
        changed = False
        if lang == DEFAULT_LANG:
            entry = data.pop(old_slug, None)
            if entry is not None:
                entry["verified"] = False
                data[new_slug] = entry
                changed = True
        else:
            for key, entry in data.items():
                if (entry or {}).get("en") == old_slug:
                    entry["en"] = new_slug
                    entry["verified"] = False
                    changed = True
        if changed:
            self.write_translations(data)


# --------------------------------------------------------------- translation

# Mirrors the router's builtin "translate-to-pl" prompt, pointed at English,
# because /api/translate can only produce Polish.
TRANSLATE_TO_EN_SYSTEM_PROMPT = """You are a professional text translator.

Task:
- Your task is to translate the text provided by the user.
- The language you translate to is English.
- Never translate into another language.

Rules:
- Treat every user utterance as text to be translated.
- If the user asks something, do not answer the question, just translate it.
- Never change the meaning of the translated text.
- If the text is written in Markdown, keep the Markdown structure: headings,
  emphasis, links, images, lists and code blocks must stay intact; translate
  only the human-readable words, never file paths, code, URLs or placeholders.
- If the text to be translated is already in the target language:
  + return the text exactly as it is, regardless of how it is written
  + do not add a note that the text is already in the target language
  + do not "improve" the form — return it in exactly the same form
- Never add anything yourself; return only the translated text."""

DEFAULT_MAX_NEW_TOKENS = 8192


def _default_llm_router_repo() -> Path:
    """The llm-router checkout next to the develop/ tree this repo lives in."""
    env = os.environ.get("LLM_ROUTER_REPO")
    if env:
        return Path(env)
    return ROOT.parents[2] / "llm-router"


class Translator:
    """Thin wrapper around LLMRouterClient for post translation."""

    def __init__(self, api: Optional[str] = None, token: Optional[str] = None,
                 model: Optional[str] = None, timeout: int = 300, retries: int = 2):
        api = api or os.environ.get("LLM_ROUTER_API", "http://127.0.0.1:8080")
        if token is None:
            token = os.environ.get("LLM_ROUTER_TOKEN") or None
        repo = _default_llm_router_repo()
        if repo.is_dir() and str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        try:
            from llm_router_lib.client import LLMRouterClient
        except ImportError as exc:
            raise PostError(
                f"nie można zaimportować llm_router_lib (repo: {repo}) — "
                "ustaw LLM_ROUTER_REPO na ścieżkę do llm-router"
            ) from exc
        self.client = LLMRouterClient(api=api, token=token, timeout=timeout,
                                      retries=retries, default_model=model)
        self.api = api

    def close(self) -> None:
        self.client.close()

    def ping(self) -> bool:
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        return list(self.client.models().ids)

    def translate_texts(self, target_lang: str, texts: list[str],
                        model: Optional[str] = None,
                        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
                        progress: Optional[ProgressFn] = None) -> list[str]:
        """Translate ``texts`` into ``target_lang``; one result per input."""
        texts = [text if isinstance(text, str) else str(text) for text in texts]
        if not texts:
            return []
        model = model or self.client.default_model
        if not model:
            raise PostError("nie wybrano modelu tłumaczącego (wybierz model w oknie tłumaczenia)")
        if target_lang == "pl":
            response = self.client.translate(texts=texts, model=model,
                                             max_new_tokens=max_new_tokens)
            return [item.translated for item in response.response]
        results: list[str] = []
        for index, text in enumerate(texts, start=1):
            response = self.client.extended_conversation_with_model(
                system_prompt=TRANSLATE_TO_EN_SYSTEM_PROMPT,
                user_last_statement=text,
                model=model,
                max_new_tokens=max_new_tokens,
            )
            results.append(response.response)
            if progress:
                progress(index, len(texts), text)
        return results


# ------------------------------------------------------------- post workflow

# (field name, label for the progress bar, tokens budget for that field)
TRANSLATABLE_FIELDS: tuple[tuple[str, str, int], ...] = (
    ("title", "tytuł", 512),
    ("description", "opis", 2048),
    ("tags", "tagi", 1024),
    ("categories", "kategorie", 1024),
    ("body", "treść", DEFAULT_MAX_NEW_TOKENS),
)


def collect_translatable(source: LoadedPost) -> "OrderedDict[str, list[str]]":
    """Fields of a post that go through the model, in a stable order."""
    meta = source.meta
    return OrderedDict([
        ("title", [str(meta.get("title") or source.slug)]),
        ("description", [str(meta.get("description") or "")]),
        ("tags", [str(tag) for tag in (meta.get("tags") or [])]),
        ("categories", [str(tag) for tag in (meta.get("categories") or [])]),
        ("body", [source.body]),
    ])


def build_translated_meta(source: LoadedPost, translated: "OrderedDict[str, list[str]]",
                          target_lang: str, target_slug: str,
                          *, make_draft: bool = True) -> "OrderedDict[str, object]":
    """Assemble the front matter for the translated copy."""
    meta: "OrderedDict[str, object]" = OrderedDict()
    title = (translated.get("title") or [""])[0].strip()
    meta["title"] = title or str(source.meta.get("title", source.slug))
    date = source.meta.get("date")
    if date:
        if isinstance(date, str):
            date = dt.date.fromisoformat(date[:10])
        meta["date"] = date
    meta["updated"] = dt.date.today()
    meta["slug"] = target_slug
    description = (translated.get("description") or [""])[0].strip()
    if description:
        meta["description"] = description
    tags = [tag.strip() for tag in translated.get("tags", []) if tag and tag.strip()]
    if tags:
        meta["tags"] = tags
    categories = [item.strip() for item in translated.get("categories", [])
                  if item and item.strip()]
    if categories:
        meta["categories"] = categories
    image = source.meta.get("image")
    if image:
        meta["image"] = image
    meta["lang"] = target_lang
    if target_lang != DEFAULT_LANG:
        meta["translation_of"] = source.slug
    if make_draft:
        meta["draft"] = True
    return meta


def copy_post_media(source: LoadedPost, target: ContentStore, lang: str,
                    slug: str) -> int:
    """Copy the post's media/ directory to the target post; returns file count."""
    source_media = source.path.parent / "media"
    if not source_media.is_dir():
        return 0
    target_media = target.post_dir(lang, slug) / "media"
    target_media.mkdir(parents=True, exist_ok=True)
    copied = 0
    for file in sorted(source_media.rglob("*")):
        if not file.is_file():
            continue
        destination = target_media / file.relative_to(source_media)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destination)
        copied += 1
    return copied


def translate_post(store: ContentStore, source_lang: str, source_slug: str,
                   target_lang: str, translator: Translator,
                   *, model: Optional[str] = None, make_draft: bool = True,
                   max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
                   overwrite: bool = False,
                   progress: Optional[ProgressFn] = None) -> LoadedPost:
    """Translate one post into the other language and write the result.

    The result is a draft (unless ``make_draft=False``), linked in
    ``config/translations.json`` with ``verified: false``; media files are
    copied so relative ``media/...`` paths keep working in the builder.
    ``progress`` is called as ``progress(done_fields, total_fields, field)``.
    """
    if source_lang not in LANGS or target_lang not in LANGS:
        raise PostError(f"nieobsługiwany język: {source_lang} -> {target_lang}")
    if source_lang == target_lang:
        raise PostError("tłumaczenie wymaga dwóch różnych języków")
    source = store.load_post(source_lang, source_slug)

    counterpart = store.find_counterpart(source_lang, source_slug)
    if counterpart and not overwrite:
        raise PostExists(f"istnieje już tłumaczenie {target_lang}/{counterpart} — "
                         "zaznacz nadpisanie, aby przetłumaczyć ponownie")
    target_slug = counterpart or ""

    fields = collect_translatable(source)
    total_fields = len(TRANSLATABLE_FIELDS)
    done = 0
    for name, label, field_tokens in TRANSLATABLE_FIELDS:
        chunk = fields.get(name) or []
        if not chunk:
            done += 1
            if progress:
                progress(done, total_fields, label)
            continue
        budget = max_new_tokens if name == "body" else field_tokens
        fields[name] = translator.translate_texts(
            target_lang, chunk, model=model, max_new_tokens=budget,
        )
        done += 1
        if progress:
            progress(done, total_fields, label)

    translated_title = (fields.get("title") or [""])[0].strip()
    if not target_slug:
        target_slug = unique_slug(store, target_lang, slugify(translated_title))

    meta = build_translated_meta(source, fields, target_lang, target_slug,
                                 make_draft=make_draft)
    body = (fields.get("body") or [source.body])[0]
    store.save_post(target_lang, target_slug, meta, body)
    copy_post_media(source, store, target_lang, target_slug)
    pl_slug = source_slug if source_lang == DEFAULT_LANG else target_slug
    en_slug = target_slug if source_lang == DEFAULT_LANG else source_slug
    store.link_translation(pl_slug, en_slug, verified=False)
    return store.load_post(target_lang, target_slug)
