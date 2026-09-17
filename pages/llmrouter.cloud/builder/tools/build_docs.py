#!/usr/bin/env python3
"""Generate the llm-router documentation site from the Markdown files in the
source repository (the llm-router checkout).

Every page under ``site/docs`` is derived from a Markdown file that lives in
that repository, so publishing documentation means committing the ``.md``
file there. Pages are grouped into the sections declared in
``tools/docs.toml`` and archived per release: ``/docs`` always shows the
version from ``.version`` and every release tag gets a frozen copy of the
documentation next to it.

The source defaults to this repo (legacy single-repo layout); point the
builder at the llm-router checkout with ``--source``:

    python3 tools/build_docs.py --source /path/to/llm-router
    python3 tools/build_docs.py --source /path/to/llm-router --all-versions
    python3 tools/build_docs.py --serve          # build, then http://localhost:8000
"""

from __future__ import annotations

import argparse
import functools
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "tools" / "docs.toml"
DEFAULT_OUTPUT = REPO_ROOT / "site"
THEME_DIR = REPO_ROOT / "tools" / "theme"
VENV_DIR = REPO_ROOT / ".venv-docs"
REQUIREMENTS = REPO_ROOT / "tools" / "requirements-docs.txt"
SOURCE_ENV = "LLM_ROUTER_DOCS_SOURCE"
# Repository the documentation is generated from; set in main() from
# --source / $LLM_ROUTER_DOCS_SOURCE / [site] source_repo (default: REPO_ROOT).
SOURCE_ROOT: Path = REPO_ROOT
BOOTSTRAP_FLAG = "LLM_ROUTER_DOCS_BOOTSTRAPPED"

DOCS_DIR_NAME = "docs"
ASSETS_DIR_NAME = "assets"
VERSIONS_FILE = "versions.json"
PRERELEASE_MARKER = "-"
PYGMENTS_STYLE = "one-dark"


# --------------------------------------------------------------------------- #
# dependency bootstrap
# --------------------------------------------------------------------------- #
def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def has_markdown() -> bool:
    try:
        import markdown  # noqa: F401
        import pygments  # noqa: F401
    except ImportError:
        return False
    return True


def bootstrap_dependencies(quiet: bool) -> None:
    """Create .venv-docs/ with the builder dependencies and re-exec into it."""
    if has_markdown():
        return
    interpreter = venv_python()
    if interpreter.exists():
        os.environ[BOOTSTRAP_FLAG] = "1"
        os.execv(str(interpreter), [str(interpreter), str(__file__)] + sys.argv[1:])
    if os.environ.get(BOOTSTRAP_FLAG):
        raise SystemExit(
            "the .venv-docs interpreter is missing markdown/pygments -- recreate it:\n"
            f"  rm -rf {VENV_DIR} && python3 -m venv {VENV_DIR} && "
            f"{VENV_DIR}/bin/pip install -r {REQUIREMENTS}"
        )
    if not quiet:
        print(f"[docs] bootstrapping {VENV_DIR} ...", flush=True)
    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)], check=True, cwd=REPO_ROOT
    )
    subprocess.run(
        [
            str(interpreter),
            "-m",
            "pip",
            "install",
            "--quiet",
            "-r",
            str(REQUIREMENTS),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    os.environ[BOOTSTRAP_FLAG] = "1"
    os.execv(str(interpreter), [str(interpreter), str(__file__)] + sys.argv[1:])


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
@dataclass
class Section:
    id: str
    title: str
    summary: str = ""
    patterns: tuple[str, ...] = ()


@dataclass
class PageOverride:
    title: str | None = None
    out: str | None = None
    order: int = 100
    summary: str | None = None
    adapter: str | None = None


@dataclass
class Config:
    site: dict
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    fallback_section: str
    sections: list[Section]
    overrides: dict[str, PageOverride]
    source_repo: str | None = None

    @property
    def title(self) -> str:
        return str(self.site.get("title", "documentation"))

    @property
    def repo_url(self) -> str:
        return str(self.site.get("repo_url", "")).rstrip("/")

    @property
    def site_url(self) -> str:
        return str(self.site.get("site_url", "")).rstrip("/")

    def section(self, section_id: str) -> Section:
        for section in self.sections:
            if section.id == section_id:
                return section
        return Section(section_id, section_id.replace("-", " ").title())

    def section_for(self, source: str) -> Section:
        for section in self.sections:
            for pattern in section.patterns:
                if path_matches(source, pattern):
                    return section
        return self.section(self.fallback_section)

    def override_for(self, source: str) -> PageOverride:
        return self.overrides.get(source, PageOverride())


def load_config(path: Path) -> Config:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    sections = [
        Section(
            id=str(item["id"]),
            title=str(item.get("title", item["id"])),
            summary=str(item.get("summary", "")),
            patterns=tuple(str(pattern) for pattern in item.get("match", [])),
        )
        for item in raw.get("sections", [])
    ]
    overrides: dict[str, PageOverride] = {}
    for item in raw.get("pages", []):
        source = normalize_path(str(item["path"]))
        overrides[source] = PageOverride(
            title=item.get("title"),
            out=item.get("out"),
            order=int(item.get("order", 100)),
            summary=item.get("summary"),
            adapter=item.get("adapter"),
        )
    discover = raw.get("discover", {})
    site = raw.get("site", {})
    source_repo = site.get("source_repo")
    return Config(
        site=site,
        include=tuple(str(item) for item in discover.get("include", ["**/*.md"])),
        exclude=tuple(str(item) for item in discover.get("exclude", [])),
        fallback_section=str(discover.get("fallback_section", "other")),
        sections=sections,
        overrides=overrides,
        source_repo=str(source_repo).strip() if source_repo else None,
    )


def resolve_source_root(cli_value: Path | None, config: Config) -> Path:
    """Resolve the source repository.

    Precedence: ``--source`` > ``$LLM_ROUTER_DOCS_SOURCE`` > ``[site]
    source_repo`` > this repo (legacy layout). Relative paths are resolved
    against the current working directory.
    """
    raw: str | Path | None = cli_value
    if raw is None:
        raw = os.environ.get(SOURCE_ENV, "").strip() or None
    if raw is None and config.source_repo:
        raw = config.source_repo
    if raw is None:
        raw = REPO_ROOT
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.is_dir():
        raise SystemExit(f"[docs] source path is not a directory: {path}")
    return path


# --------------------------------------------------------------------------- #
# git helpers
# --------------------------------------------------------------------------- #
def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=SOURCE_ROOT, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise SystemExit(
            f"[docs] git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout


def git_ok() -> bool:
    """True when the source root is a git work tree (history/tags available)."""
    return git("rev-parse", "--git-dir", check=False).strip() != ""


def normalize_path(path: str) -> str:
    cleaned = path.replace(os.sep, "/").replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip("/")


def tracked_files(ref: str) -> list[str]:
    if ref == "":
        paths: list[str] = []
        for root, dirs, files in os.walk(SOURCE_ROOT):
            dirs[:] = sorted(
                name
                for name in dirs
                if not name.startswith(".")
                and not name.endswith((".egg-info", ".venv-docs"))
            )
            for name in sorted(files):
                full = Path(root) / name
                paths.append(str(full.relative_to(SOURCE_ROOT)))
        return paths
    output = git("ls-tree", "-r", "--name-only", "-z", ref)
    return [entry for entry in output.split("\0") if entry]


def read_content(ref: str, source: str) -> str:
    if ref == "":
        return (SOURCE_ROOT / source).read_text(encoding="utf-8", errors="replace")
    result = subprocess.run(
        ["git", "show", f"{ref}:{source}"],
        cwd=SOURCE_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(f"[docs] cannot read {ref}:{source}")
    return result.stdout


# --------------------------------------------------------------------------- #
# releases
# --------------------------------------------------------------------------- #
@dataclass
class Release:
    version: str
    ref: str
    source: str
    tag: str | None
    date: str
    sha: str
    prerelease: bool
    pages: list["Page"] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.prerelease:
            return f"{self.version} (pre-release)"
        return self.version

    @property
    def read_ref(self) -> str:
        """Ref to read file contents from; empty means the working tree."""
        return "" if self.source == "worktree" else self.ref


def version_key(version: str) -> tuple:
    core, _, extra = version.partition(PRERELEASE_MARKER)
    numbers = tuple(int(part) for part in re.findall(r"\d+", core)[:4])
    return (numbers, extra == "", extra)


def is_prerelease(version: str) -> bool:
    return PRERELEASE_MARKER in version


def current_release() -> Release:
    version_file = SOURCE_ROOT / ".version"
    version = (
        version_file.read_text(encoding="utf-8").strip()
        if version_file.exists()
        else "0.0.0"
    )
    if not git_ok():
        stamp = (
            datetime.fromtimestamp(
                version_file.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            if version_file.exists()
            else "unknown"
        )
        return Release(
            version=version,
            ref=SOURCE_ROOT.name or "source",
            source="worktree",
            tag=None,
            date=stamp,
            sha="unknown",
            prerelease=is_prerelease(version),
        )
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "HEAD":
        branch = (
            git("describe", "--tags", "--exact-match", "HEAD", check=False).strip()
            or "HEAD"
        )
    sha = git("rev-parse", "--short", "HEAD").strip()
    date = git("log", "-1", "--format=%cI", "HEAD").strip()
    return Release(
        version=version,
        ref=branch,
        source="worktree",
        tag=None,
        date=date,
        sha=sha,
        prerelease=is_prerelease(version),
    )


def collect_releases(
    include_prerelease: bool, max_versions: int | None
) -> list[Release]:
    working = current_release()
    releases = [working]
    tags = git("tag").split() if git_ok() else []
    for tag in tags:
        version = tag[1:] if tag.startswith("v") else tag
        if version == working.version:
            continue
        if is_prerelease(version) and not include_prerelease:
            continue
        date = git("log", "-1", "--format=%cI", tag).strip()
        sha = git("rev-parse", "--short", f"{tag}^{{commit}}").strip()
        releases.append(
            Release(
                version=version,
                ref=tag,
                source="tag",
                tag=tag,
                date=date,
                sha=sha,
                prerelease=is_prerelease(version),
            )
        )
    releases.sort(key=lambda item: version_key(item.version), reverse=True)
    if max_versions is not None:
        releases = releases[:max_versions]
    return releases


# --------------------------------------------------------------------------- #
# documents
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=1024)
def glob_regex(pattern: str) -> re.Pattern[str]:
    """Compile a repository relative glob into a path aware regular expression.

    ``?`` matches one character, ``*`` a single path segment and ``**`` any
    number of segments. Slices of a path are therefore significant, which is
    what makes ``**/*.md`` cover the documents in the repository root too.
    """
    parts: list[str] = []
    segments = [item for item in pattern.strip("/").split("/") if item]
    needs_separator = False
    for position, segment in enumerate(segments):
        final = position == len(segments) - 1
        if segment == "**":
            if not parts:
                parts.append(".*" if final else "(?:[^/]*/)*")
            else:
                parts.append("(?:/.*)?" if final else "(?:[^/]*/)*")
            needs_separator = False
            continue
        if needs_separator:
            parts.append("/")
        translated: list[str] = []
        for char in segment:
            if char == "*":
                translated.append("[^/]*")
            elif char == "?":
                translated.append("[^/]")
            else:
                translated.append(re.escape(char))
        parts.append("".join(translated))
        needs_separator = True
    return re.compile("".join(["^", *parts, "$"]))


def path_matches(path: str, pattern: str) -> bool:
    return glob_regex(pattern).match(path) is not None


def is_documentation(path: str, config: Config) -> bool:
    if not path.lower().endswith(".md"):
        return False
    if any(path_matches(path, pattern) for pattern in config.exclude):
        return False
    return any(path_matches(path, pattern) for pattern in config.include)


def slug_part(value: str) -> str:
    cleaned = value.lower().replace("_", "-").replace(" ", "-")
    cleaned = re.sub(r"[^a-z0-9.-]+", "-", cleaned).strip("-.")
    return cleaned or "page"


def output_path(source: str, override: PageOverride) -> str:
    if override.out:
        return override.out.strip("/")
    parent = posixpath.dirname(source)
    stem = posixpath.splitext(posixpath.basename(source))[0]
    name = "index.html" if stem.lower() == "readme" else slug_part(stem) + ".html"
    parts = [slug_part(part) for part in parent.split("/") if part]
    return "/".join([*parts, name])


@dataclass
class Page:
    source: str
    out: str
    title: str
    section: str
    summary: str
    order: int
    adapter: str | None = None
    markdown: str = ""
    html_body: str = ""
    toc: list = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    excerpt: str = ""


# --------------------------------------------------------------------------- #
# markdown helpers
# --------------------------------------------------------------------------- #
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
ATX_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
CODE_BLOCK_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,}).*?^\1[ \t]*$", re.S | re.M)


def strip_inline(value: str) -> str:
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"`+([^`]*)`+", r"\1", value)
    value = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", value)
    return value.strip()


def first_heading(text: str) -> tuple[str | None, int | None]:
    """Return the text and line index of the first ATX heading outside fences."""
    fence: str | None = None
    for index, line in enumerate(text.splitlines()):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)[0]
            fence = marker if fence is None else None
            continue
        if fence:
            continue
        heading = ATX_RE.match(line)
        if heading:
            return strip_inline(heading.group(2)), index
    return None, None


def with_title(text: str, title: str) -> str:
    """Make sure the document starts with an h1 carrying the page title."""
    existing, index = first_heading(text)
    if index is None:
        return f"# {title}\n\n{text.lstrip()}"
    lines = text.splitlines()
    lines[index] = f"# {strip_inline(lines[index].lstrip('#').strip()) or title}"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def plain_text(text: str, limit: int | None = None) -> str:
    """Readable text of a Markdown document: no code, tables or headings."""
    body = CODE_BLOCK_RE.sub(" ", text)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    kept: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", ">", "!", "<")):
            continue
        if set(stripped) <= set("-*:~ "):
            continue
        kept.append(stripped)
    joined = re.sub(r"\s+", " ", strip_inline(" ".join(kept))).strip()
    if limit is not None and len(joined) > limit:
        joined = joined[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"
    return joined


# --------------------------------------------------------------------------- #
# adapters
# --------------------------------------------------------------------------- #
def changelog_adapter(text: str) -> str:
    """Turn the two-column CHANGELOG table into a per-release list.

    Rows are parsed by splitting on the first pipe only, because the changelog
    cells contain unescaped pipes inside inline code.
    """
    releases: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        version, separator, rest = stripped[1:].partition("|")
        if not separator:
            continue
        version = version.strip().strip("`")
        if not re.match(r"^\d+\.\d+", version):
            continue
        body = rest.rstrip()
        if body.endswith("|"):
            body = body[:-1]
        releases.append((version, body.replace("\\|", "|")))
    if not releases:
        return text
    chunks = ["# Changelog"]
    for version, body in releases:
        items = [
            item.strip()
            for chunk in re.split(r"(?<=\.)[ \t]{2,}", body)
            for item in re.split(r"(?<=\.)[ \t]+(?=\*\*)", chunk)
            if item.strip()
        ]
        chunks.append(f"\n## {version}")
        if len(items) == 1:
            chunks.append(f"\n{items[0]}\n")
        else:
            chunks.append("")
            chunks.extend(f"- {item}" for item in items)
            chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


ADAPTERS = {"changelog": changelog_adapter}


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "tables",
    "def_list",
    "admonition",
    "toc",
]
MARKDOWN_CONFIG = {
    "codehilite": {"css_class": "codehilite", "guess_lang": False},
    "toc": {
        "toc_depth": "2-3",
        "permalink": "#",
        "permalink_class": "headerlink",
        "permalink_title": "link to this section",
    },
}

LINK_RE = re.compile(r'(<a\b[^>]*?href=")([^"]*)("[^>]*>)')
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


class Href:
    """Resolve site-root-relative targets against the directory of a page."""

    def __init__(self, from_dir: str = "") -> None:
        self.from_dir = from_dir or "."

    def to(self, target: str) -> str:
        clean = target.lstrip("/")
        return posixpath.normpath(posixpath.relpath(clean, self.from_dir))

    def versioned(self, version_dir: str, target: str) -> str:
        return self.to(posixpath.join(version_dir, target))


def new_markdown():
    import markdown

    return markdown.Markdown(
        extensions=MARKDOWN_EXTENSIONS, extension_configs=MARKDOWN_CONFIG
    )


def external_attrs(tag_attrs: str) -> str:
    attrs = tag_attrs
    if "target=" not in attrs:
        attrs += ' target="_blank"'
    if "rel=" not in attrs:
        attrs += ' rel="noopener noreferrer"'
    return attrs


def rewrite_links(
    body: str,
    page: Page,
    release: Release,
    index: dict[str, Page],
    tree_files: set[str],
    tree_dirs: set[str],
    config: Config,
    unresolved: list[str],
) -> str:
    from_dir = posixpath.dirname(page.out)
    href = Href(from_dir)

    def replace(match: re.Match) -> str:
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        if not target or target.startswith("#"):
            return match.group(0)
        if SCHEME_RE.match(target) or target.startswith("//"):
            return f"{prefix}{target}{external_attrs(suffix)}"
        path_part, _, anchor = target.partition("#")
        if not path_part:
            return match.group(0)
        if path_part.startswith("/"):
            candidate = posixpath.normpath(path_part.lstrip("/"))
        else:
            candidate = posixpath.normpath(
                posixpath.join(posixpath.dirname(page.source), path_part)
            )
        candidate = candidate.removeprefix("./")
        anchor_suffix = f"#{anchor}" if anchor else ""
        wants = [candidate]
        if not path_part.startswith(".."):
            # some documents link repo-root relative, so resolve it both ways
            root = posixpath.normpath(path_part)
            if root != candidate:
                wants.append(root)
        link = ""
        blob = f"{config.repo_url}/blob/{quote(release.ref)}"
        for want in wants:
            stem_only = bool(want) and not posixpath.splitext(want)[1]
            with_md = want + ".md"
            if want in index:
                out = index[want].out
                return f"{prefix}{href.to(out)}{anchor_suffix}{suffix}"
            if stem_only and with_md in index:
                out = index[with_md].out
                return f"{prefix}{href.to(out)}{anchor_suffix}{suffix}"
            if want in tree_dirs:
                link = f"{config.repo_url}/tree/{quote(release.ref)}/{quote(want)}"
                break
            if want in tree_files:
                link = f"{blob}/{quote(want)}"
                break
            if stem_only and with_md in tree_files:
                link = f"{blob}/{quote(with_md)}"
                break
        else:
            unresolved.append(f"{page.source} -> {target}")
            link = f"{blob}/{quote(candidate)}"
        return f"{prefix}{link}{external_attrs(suffix)}"

    return LINK_RE.sub(replace, body)


def render_toc(tokens: list) -> str:
    if not tokens:
        return '<p class="dtoc-empty">no headings</p>'

    def walk(items: list) -> str:
        parts = ["<ul>"]
        for item in items:
            children = walk(item["children"]) if item.get("children") else ""
            parts.append(
                f'<li><a href="#{html.escape(item["id"], quote=True)}">'
                f'{html.escape(item["name"])}</a>{children}</li>'
            )
        parts.append("</ul>")
        return "".join(parts)

    return walk(tokens)


# --------------------------------------------------------------------------- #
# collecting the documents of a release
# --------------------------------------------------------------------------- #
_TREE_CACHE: dict[str, list[str]] = {}


def tree_paths(ref: str) -> tuple[set[str], set[str]]:
    """Files and directories that exist for a ref, used to resolve links."""
    if ref not in _TREE_CACHE:
        _TREE_CACHE[ref] = tracked_files(ref)
    files = set(_TREE_CACHE[ref])
    directories: set[str] = set()
    for path in files:
        parent = posixpath.dirname(path)
        while parent:
            directories.add(parent)
            parent = posixpath.dirname(parent)
    return files, directories


def unique_output(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        used.add(candidate)
        return candidate
    stem, extension = posixpath.splitext(candidate)
    counter = 2
    while f"{stem}-{counter}{extension}" in used:
        counter += 1
    result = f"{stem}-{counter}{extension}"
    used.add(result)
    return result


def section_order(config: Config) -> dict[str, int]:
    return {section.id: position for position, section in enumerate(config.sections)}


def sort_pages(pages: list[Page], order: dict[str, int]) -> list[Page]:
    return sorted(
        pages,
        key=lambda page: (
            order.get(page.section, len(order)),
            page.order,
            page.title.lower(),
        ),
    )


def collect_pages(release: Release, config: Config) -> list[Page]:
    used: set[str] = {"index.html"}
    pages: list[Page] = []
    for source in sorted(tracked_files(release.read_ref), key=str.lower):
        if not is_documentation(source, config):
            continue
        override = config.override_for(source)
        document = read_content(release.read_ref, source)
        if override.adapter:
            adapter = ADAPTERS.get(override.adapter)
            if adapter is None:
                raise SystemExit(
                    f"[docs] {source}: unknown adapter '{override.adapter}' "
                    f"(known: {', '.join(sorted(ADAPTERS))})"
                )
            document = adapter(document)
        section = config.section_for(source)
        extracted, _ = first_heading(document)
        title = (
            override.title
            or extracted
            or slug_part(source).replace("-", " ").title()
        )
        pages.append(
            Page(
                source=source,
                out=unique_output(output_path(source, override), used),
                title=title,
                section=section.id,
                summary=override.summary or section.summary,
                order=override.order,
                adapter=override.adapter,
                markdown=with_title(document, title),
                excerpt=plain_text(document, 240),
            )
        )
    if not pages:
        raise SystemExit(
            f"[docs] no Markdown documents found for {release.ref or 'worktree'}"
        )
    release.pages = sort_pages(pages, section_order(config))
    return release.pages


def flatten_toc(tokens: list) -> list[dict]:
    flat: list[dict] = []
    for token in tokens:
        flat.append(token)
        flat.extend(flatten_toc(token.get("children", [])))
    return flat


def render_documents(release: Release, config: Config) -> list[str]:
    """Convert every page of a release to HTML and fix up internal links."""
    engine = new_markdown()
    files, directories = tree_paths(release.read_ref)
    index = {page.source: page for page in release.pages}
    unresolved: list[str] = []
    for page in release.pages:
        body = engine.convert(page.markdown)
        page.toc = list(getattr(engine, "toc_tokens", []))
        page.headings = [str(token["name"]) for token in flatten_toc(page.toc)]
        page.html_body = rewrite_links(
            body, page, release, index, files, directories, config, unresolved
        )
    return unresolved


# --------------------------------------------------------------------------- #
# html templates
# --------------------------------------------------------------------------- #
BRAND_SVG = (
    '<svg width="21" height="21" viewBox="0 0 32 32" aria-hidden="true">'
    '<rect width="32" height="32" rx="7" fill="#0b1119" stroke="#1a232e"/>'
    '<path d="M8 22V10M8 16h9M17 10v12M17 13h7M17 19h7" stroke="#00e59b" '
    'stroke-width="2" stroke-linecap="round" fill="none"/></svg>'
)
GITHUB_SVG = (
    '<svg width="17" height="17" viewBox="0 0 16 16" aria-hidden="true"><path '
    'fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 '
    "7.59c.4.07.55-.17.55-.38 "
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.2"
    "8-.15-.68-.52-.46-.53.42-.02.72.39.82.55.48.81 1.25.94 "
    "1.56.73.2-.27.6-.94.94-1.13-.01-.2-.05-.82-.14-.98-.6.1-1.22.2-1.87.2-1.9 "
    "0-3.62-1.13-3.62-3.53 0-.78.28-1.42.74-1.92-.07-.18-.32-.91.07-1.9 0 0 "
    ".6-.19 1.97.74a6.8 6.8 0 0 1 3.58 0c1.37-.93 1.97-.74 1.97-.74.39.99.14 "
    "1.72.07 1.9.46.5.74 1.14.74 1.92 0 2.41-1.47 3.53-3.87 3.72.3.26.57.77.57 "
    "1.56 0 1.13-.012.04-.01 2.32 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 "
    '8c0-4.42-3.58-8-8-8Z"/></svg>'
)
FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 "
    "32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2305070a'/%3E%3Cpath "
    "d='M8 22V10M8 16h9M17 10v12M17 13h7M17 19h7' stroke='%2300e59b' "
    "stroke-width='2' stroke-linecap='round' fill='none'/%3E%3C/svg%3E"
)

SHELL_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#05070a">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta name="docs-version" content="{version}">{canonical}
<link rel="icon" href="{favicon}">
<link rel="stylesheet" href="{css}">
<link rel="stylesheet" href="{syntax}">
<script src="{js}" defer></script>
</head>
<body class="{body_class}" data-version="{version}" \
data-search="{search}" data-latest="{latest}">
<a class="skip" href="#main">skip to content</a>
<header class="topbar">
<div class="topbar-inner">
<button class="burger" id="burger" aria-label="Toggle documentation menu" \
aria-expanded="false" aria-controls="sidebar">&#9776;</button>
<a class="brand" href="{home}">{brand}<span>llm<span class="dash">-</span>router</span>\
<span class="brand-docs">/docs</span></a>
<div class="topbar-right">
<form class="search" id="search" role="search" autocomplete="off">
<span class="search-icon" aria-hidden="true">&#8981;</span>
<input id="q" type="search" placeholder="search this version" \
aria-label="Search documentation" role="combobox" aria-expanded="false" \
aria-controls="results" aria-autocomplete="list">
<kbd>/</kbd>
<div class="results" id="results" role="listbox" \
aria-label="Search results" hidden></div>
</form>
<label class="vselect">
<span class="sr-only">Documentation version</span>
<select id="versions" aria-label="Documentation version">{versions}</select>
</label>
<a class="iconbtn" href="{repo}" aria-label="Repository on GitHub" \
title="Repository on GitHub">{github}</a>
</div>
</div>
</header>
<div class="scrim" id="scrim" hidden></div>
<div class="shell">
<aside class="sidebar" id="sidebar">{sidebar}</aside>
<main class="main" id="main">{main}
<footer class="foot"><div class="foot-inner">
<span class="mono">llm-router &middot; docs are generated from the repository by \
<code>tools/build_docs.py</code></span>
<span class="mono"><a href="{blob}">{version}</a> @ <code>{sha}</code></span>
</div></footer>
</main>
<aside class="dtoc" id="dtoc">{toc}</aside>
</div>
</body>
</html>
"""


@dataclass
class VersionEntry:
    """One entry of versions.json: a published documentation snapshot."""

    version: str
    entry: str
    date: str = ""
    prerelease: bool = False
    ref: str = ""
    sha: str = ""
    pages: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str:
        if self.prerelease:
            return f"{self.version} (pre-release)"
        return self.version

    @staticmethod
    def from_release(release: Release) -> "VersionEntry":
        return VersionEntry(
            version=release.version,
            entry=posixpath.join(release.version, "index.html"),
            date=release.date,
            prerelease=release.prerelease,
            ref=release.ref,
            sha=release.sha,
            pages={page.source: page.out for page in release.pages},
        )

    @staticmethod
    def from_json(raw: dict) -> "VersionEntry":
        version = str(raw["version"])
        return VersionEntry(
            version=version,
            entry=str(raw.get("entry") or posixpath.join(version, "index.html")),
            date=str(raw.get("date", "")),
            prerelease=bool(raw.get("prerelease", False)),
            ref=str(raw.get("ref", "")),
            sha=str(raw.get("sha", "")),
            pages={
                str(key): str(value)
                for key, value in (raw.get("pages") or {}).items()
            },
        )

    def as_json(self) -> dict:
        return {
            "version": self.version,
            "entry": self.entry,
            "date": self.date,
            "prerelease": self.prerelease,
            "ref": self.ref,
            "sha": self.sha,
            "pages": self.pages,
        }


def sort_versions(entries: list[VersionEntry]) -> list[VersionEntry]:
    return sorted(entries, key=lambda item: version_key(item.version), reverse=True)


def short_date(value: str) -> str:
    return value[:10] if value else "unknown"


def render_version_options(
    page_source: str,
    release: Release,
    versions: list[VersionEntry],
    latest: str,
    page_dir: str,
) -> str:
    """Version switcher: same document when the other version has it, hub otherwise."""
    href = Href(page_dir)
    options: list[str] = []
    for entry in versions:
        target = entry.entry
        if page_source and page_source in entry.pages:
            target = posixpath.join(entry.version, entry.pages[page_source])
        attrs = [f'value="{html.escape(href.to(target), quote=True)}"']
        if entry.version == release.version:
            attrs.append("selected")
        if entry.prerelease:
            attrs.append('data-kind="pre"')
        suffix = "  \u00b7 latest" if entry.version == latest else ""
        options.append(
            f'<option {" ".join(attrs)}>{html.escape(entry.label)}{suffix}</option>'
        )
    return "\n".join(options)


def render_sidebar(
    release: Release,
    config: Config,
    current: Page | None,
    page_dir: str,
    latest: str,
    versions: list[VersionEntry],
    search_enabled: bool = True,
) -> str:
    href = Href(page_dir)
    grouped: dict[str, list[Page]] = {}
    for page in release.pages:
        grouped.setdefault(page.section, []).append(page)
    is_latest = release.version == latest
    parts: list[str] = [
        '<div class="side-head">',
        f'<span class="side-v mono">v{html.escape(release.version)}</span>',
        f'<span class="side-tag {"live" if is_latest else "old"}">'
        f'{"latest" if is_latest else "archived"}</span>',
        "</div>",
        f'<a class="side-hub" href="{href.versioned(release.version, "index.html")}">'
        "documentation index</a>",
        '<nav class="nav-tree" aria-label="Documentation">',
    ]
    for section in config.sections:
        pages = grouped.get(section.id)
        if not pages:
            continue
        is_open = bool(current and current.section == section.id) or current is None
        parts.append(
            f'<section class="nav-sec{" open" if is_open else ""}">'
            f'<h2 class="nav-sec-title">'
            f'<a href="{href.versioned(release.version, pages[0].out)}">'
            f"{html.escape(section.title)}</a></h2><ul>"
        )
        for page in pages:
            active = ' class="active"' if current and current.out == page.out else ""
            parts.append(
                f'<li><a href="{href.versioned(release.version, page.out)}"{active}>'
                f"{html.escape(page.title)}</a></li>"
            )
        parts.append("</ul></section>")
    parts.append("</nav>")
    search_link = (
        f'<a class="mono" href="{href.versioned(release.version, "search.json")}">'
        "search.json</a>"
        if search_enabled
        else ""
    )
    parts.append(
        '<div class="side-foot">'
        f'<a href="{href.to(str(config.site.get("home_url", "../")))}">'
        "&larr;&nbsp;landing page</a>"
        f"{search_link}"
        "</div>"
    )
    return "".join(parts)


def render_shell(
    *,
    config: Config,
    release: Release,
    versions: list[VersionEntry],
    latest: str,
    page_dir: str,
    title: str,
    description: str,
    sidebar: str,
    main: str,
    toc: str = "",
    body_class: str = "",
    canonical: str = "",
    page_source: str = "",
    search_enabled: bool = True,
) -> str:
    href = Href(page_dir)
    canonical_tag = ""
    if config.site_url and canonical:
        target = html.escape(posixpath.join(config.site_url, canonical), quote=True)
        canonical_tag = f'\n<link rel="canonical" href="{target}">'
    search_href = href.to(posixpath.join(release.version, "search.json"))
    options = render_version_options(
        page_source, release, versions, latest, page_dir
    )
    return SHELL_TEMPLATE.format(
        lang=html.escape(str(config.site.get("language", "en")), quote=True),
        title=html.escape(title, quote=True),
        description=html.escape(description, quote=True),
        canonical=canonical_tag,
        favicon=FAVICON,
        css=href.to(posixpath.join(ASSETS_DIR_NAME, "docs.css")),
        syntax=href.to(posixpath.join(ASSETS_DIR_NAME, "pygments.css")),
        js=href.to(posixpath.join(ASSETS_DIR_NAME, "docs.js")),
        body_class=html.escape(body_class, quote=True),
        version=html.escape(release.version, quote=True),
        search=html.escape(search_href if search_enabled else "", quote=True),
        latest=html.escape(latest, quote=True),
        home=href.to(str(config.site.get("home_url", "../"))),
        brand=BRAND_SVG,
        versions=options,
        repo=html.escape(config.repo_url, quote=True),
        github=GITHUB_SVG,
        sidebar=sidebar,
        main=main,
        toc=toc,
        blob=html.escape(f"{config.repo_url}/tree/{quote(release.ref)}", quote=True),
        sha=html.escape(release.sha, quote=True),
    )


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #
PAGE_TEMPLATE = """<nav class="crumbs" aria-label="Breadcrumb">
<a href="{home}">llm-router</a><span class="sep">/</span><a href="{hub}">docs</a>\
<span class="sep">/</span><a href="{section_href}">{section}</a>\
<span class="sep">/</span><em>{title}</em>
</nav>
<article class="prose">{body}</article>
<nav class="pager" aria-label="Previous and next page">{pager}</nav>
<footer class="doc-meta">
<div class="meta-row"><span class="meta-k">source</span>\
<a class="mono" href="{source_link}">{source}</a></div>
<div class="meta-row"><span class="meta-k">last commit</span>\
<time datetime="{modified}">{modified_label}</time></div>
<div class="meta-row"><span class="meta-k">built from</span>\
<span class="mono">{ref}&nbsp;@&nbsp;{sha}</span></div>
<p class="hint">Generated from the Markdown file in the repository: commit a \
change and the next build republishes it for every release that contains it.</p>
</footer>"""

HUB_TEMPLATE = """<section class="hub-hero">
<p class="eyebrow mono">{eyebrow}</p>
<h1>{title}</h1>
<p class="lede">{tagline}</p>
<p class="vline"><span class="vchip mono">v{version}</span>\
<span class="vmeta">{released} &middot; {pages} pages &middot; \
{sections} sections &middot; built from <code>{ref}</code> \
built from <code>{ref}</code> @ <code>{sha}</code></span></p>
<div class="hub-actions">{actions}</div>
</section>
<div class="hub-grid">
<section class="sec-cards" id="sections">{cards}</section>
<aside class="hub-side">{aside}</aside>
</div>"""

CARD_TEMPLATE = """<article class="sec-card">
<h2><a href="{href}">{title}</a></h2>
<p>{summary}</p>
<ul>{links}</ul>
{more}
</article>"""


def page_modified(ref: str, source: str, fallback: str) -> str:
    """Commit date of a single file; tags fall back to the release date (cheap)."""
    if ref == "":
        try:
            stamp = git("log", "-1", "--format=%cI", "HEAD", "--", source).strip()
        except SystemExit:
            stamp = ""
        if stamp:
            return stamp
    return fallback


def render_toc_panel(page: Page) -> str:
    if not page.toc:
        return ""
    return (
        '<h2 class="toc-title">on this page</h2>'
        f'<div class="toc-body">{render_toc(page.toc)}</div>'
    )


def render_page(
    page: Page,
    release: Release,
    config: Config,
    versions: list[VersionEntry],
    latest: str,
    search_enabled: bool = True,
) -> str:
    page_dir = "/".join(
        part for part in (release.version, posixpath.dirname(page.out)) if part
    )
    href = Href(page_dir)
    version_dir = release.version
    section = config.section(page.section)
    siblings = [item for item in release.pages if item.section == page.section]
    position = siblings.index(page)
    pager: list[str] = []
    if position:
        previous = siblings[position - 1]
        pager.append(
            f'<a class="prev" href="{href.versioned(version_dir, previous.out)}">'
            f'<span class="dir">&larr; previous</span>'
            f'<span class="pt">{html.escape(previous.title)}</span></a>'
        )
    if position + 1 < len(siblings):
        following = siblings[position + 1]
        pager.append(
            f'<a class="next" href="{href.versioned(version_dir, following.out)}">'
            f'<span class="dir">next &rarr;</span>'
            f'<span class="pt">{html.escape(following.title)}</span></a>'
        )
    modified = page_modified(release.read_ref, page.source, release.date)
    main = PAGE_TEMPLATE.format(
        home=href.to(str(config.site.get("home_url", "../"))),
        hub=href.to(posixpath.join(version_dir, "index.html")),
        section_href=href.to(posixpath.join(version_dir, siblings[0].out)),
        section=html.escape(section.title),
        title=html.escape(page.title),
        body=page.html_body,
        pager="".join(pager),
        source_link=f"{config.repo_url}/blob/{quote(release.ref)}/{quote(page.source)}",
        source=html.escape(page.source),
        modified=html.escape(modified, quote=True),
        modified_label=short_date(modified),
        ref=html.escape(release.ref, quote=True),
        sha=html.escape(release.sha, quote=True),
    )
    body_class = "page"
    if page.adapter:
        body_class += f" page-{page.adapter}"
    description = (
        page.excerpt
        or f"{page.title} \u2014 {section.title}, llm-router v{release.version}"
    )
    return render_shell(
        config=config,
        release=release,
        versions=versions,
        latest=latest,
        page_dir=page_dir,
        title=f"{page.title} \u00b7 v{release.version} \u00b7 llm-router docs",
        description=description[:300],
        sidebar=render_sidebar(
            release, config, page, page_dir, latest, versions, search_enabled
        ),
        main=main,
        toc=render_toc_panel(page),
        body_class=body_class,
        canonical=page.out,
        page_source=page.source,
        search_enabled=search_enabled,
    )


def render_hub(
    release: Release,
    config: Config,
    versions: list[VersionEntry],
    latest: str,
    page_dir: str = "",
    search_enabled: bool = True,
) -> str:
    """Landing page of a version: every section with the documents it contains."""
    href = Href(page_dir)
    version_dir = posixpath.join(release.version, "index.html")
    grouped: dict[str, list[Page]] = {}
    for page in release.pages:
        grouped.setdefault(page.section, []).append(page)
    cards: list[str] = []
    for section in config.sections:
        pages = grouped.get(section.id)
        if not pages:
            continue
        shown = pages[:5]
        links = "".join(
            f'<li><a href="{href.to(posixpath.join(release.version, page.out))}">'
            f"{html.escape(page.title)}</a></li>"
            for page in shown
        )
        remaining = len(pages) - len(shown)
        more = (
            f'<a class="more mono" '
            f'href="{href.versioned(release.version, pages[0].out)}">'
            f"+{remaining} more</a>"
            if remaining > 0
            else ""
        )
        cards.append(
            CARD_TEMPLATE.format(
                href=href.to(posixpath.join(release.version, pages[0].out)),
                title=html.escape(section.title),
                summary=html.escape(section.summary or pages[0].summary),
                links=links,
                more=more,
            )
        )
    actions = [
        f'<a class="btn primary" href="{href.versioned(release.version, "index.html")}#'
        f'sections">browse {len(release.pages)} documents</a>'
    ]
    overview = next(
        (page for page in release.pages if page.source == "README.md"), None
    )
    if overview is not None:
        actions.insert(
            0,
            f'<a class="btn primary" '
            f'href="{href.versioned(release.version, overview.out)}">'
            "start with the overview</a>",
        )
    changelog = next(
        (page for page in release.pages if "CHANGELOG" in page.source), None
    )
    if changelog is not None:
        actions.append(
            f'<a class="btn ghost" '
            f'href="{href.versioned(release.version, changelog.out)}">'
            "release notes</a>"
        )
    actions.append(
        f'<a class="btn ghost" href="{html.escape(config.repo_url, quote=True)}">'
        "repository</a>"
    )
    listings = []
    for entry in versions:
        current = " current" if entry.version == release.version else ""
        flag = " latest" if entry.version == latest else ""
        listings.append(
            f'<li class="vrow{current}{flag}">'
            f'<a href="{href.to(entry.entry)}">v{html.escape(entry.version)}</a>'
            f'<span class="mono">{short_date(entry.date)}</span>'
            f'{"<em>latest</em>" if flag else ""}</li>'
        )
    aside = "".join(
        [
            '<div class="box"><h2>this release</h2><dl>',
            f'<dt>version</dt><dd class="mono">{html.escape(release.version)}</dd>',
            f'<dt>released</dt><dd class="mono">{short_date(release.date)}</dd>',
            f'<dt>ref</dt><dd class="mono">{html.escape(release.ref)}</dd>',
            f'<dt>commit</dt><dd class="mono">{html.escape(release.sha)}</dd>',
            f'<dt>documents</dt><dd class="mono">{len(release.pages)}</dd>',
            "</dl></div>",
            '<div class="box"><h2>all versions</h2>'
            '<p class="tiny">Older releases keep the documentation of their '
            "own branch of the repository.</p>",
            f'<ul class="vlist" id="versions-list">{"".join(listings)}</ul></div>',
            '<div class="box note"><h2>how this works</h2><p>Every page here is '
            "rendered from a Markdown file committed in the repository. Nothing is "
            "copied by hand: the builder discovers <code>*.md</code> files, groups "
            "them with <code>tools/docs.toml</code> and archives the result per "
            "release tag.</p></div>",
        ]
    )
    eyebrow = (
        "operator documentation"
        if release.version == latest
        else "archived documentation"
    )
    main = HUB_TEMPLATE.format(
        eyebrow=eyebrow,
        title=html.escape(str(config.site.get("hub_title", config.title))),
        tagline=html.escape(str(config.site.get("tagline", ""))),
        version=html.escape(release.version),
        released=f"released {short_date(release.date)}",
        pages=len(release.pages),
        sections=len(grouped),
        ref=html.escape(release.ref),
        sha=html.escape(release.sha),
        actions="".join(actions),
        cards="".join(cards),
        aside=aside,
    )
    return render_shell(
        config=config,
        release=release,
        versions=versions,
        latest=latest,
        page_dir=page_dir,
        title=f"{config.title} \u00b7 v{release.version}",
        description=str(config.site.get("description", config.title)),
        sidebar=render_sidebar(
            release, config, None, page_dir, latest, versions, search_enabled
        ),
        main=main,
        toc=(
            '<h2 class="toc-title">versions</h2>'
            f'<div class="toc-body"><p class="tiny">v{html.escape(release.version)}'
            f" &middot; {len(release.pages)} documents</p></div>"
        ),
        body_class="hub",
        canonical=version_dir if page_dir else "index.html",
    )


# --------------------------------------------------------------------------- #
# search index
# --------------------------------------------------------------------------- #
TAG_RE = re.compile(r"<[^>]+>")
MAX_BODY_CHARS = 4000
MAX_HEADINGS = 80


def searchable_text(fragment: str, limit: int) -> str:
    """Plain text of a rendered page, used as the body of a search hit."""
    return plain_text(TAG_RE.sub(" ", fragment), limit)


def search_index(release: Release, config: Config) -> str:
    """Small per-version JSON index: no server side search is needed."""
    documents = []
    for page in release.pages:
        documents.append(
            {
                "k": page.out,
                "t": page.title,
                "s": config.section(page.section).title,
                "x": page.excerpt[:240],
                "h": page.headings[:MAX_HEADINGS],
                "b": searchable_text(page.html_body, MAX_BODY_CHARS),
            }
        )
    payload = {"version": release.version, "pages": documents}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def write_file(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pygments_css() -> str:
    """Syntax highlighting colours matching the site theme."""
    try:
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return ""
    for style in (PYGMENTS_STYLE, "default"):
        try:
            return HtmlFormatter(style=style).get_style_defs(".codehilite")
        except ValueError:
            continue
    return ""


def write_assets(docs_root: Path, dry_run: bool) -> list[str]:
    names = ["docs.css", "docs.js"]
    written: list[str] = []
    for name in names:
        source = THEME_DIR / name
        if not source.exists():
            raise SystemExit(f"[docs] missing theme file: {source}")
        if not dry_run:
            (docs_root / ASSETS_DIR_NAME).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, docs_root / ASSETS_DIR_NAME / name)
        written.append(f"{ASSETS_DIR_NAME}/{name}")
    write_file(docs_root / ASSETS_DIR_NAME / "pygments.css", pygments_css(), dry_run)
    written.append(f"{ASSETS_DIR_NAME}/pygments.css")
    return written


def read_versions(
    path: Path, docs_root: Path, clean: bool
) -> dict[str, VersionEntry]:
    """Previously published versions, so a partial build keeps them selectable."""
    entries: dict[str, VersionEntry] = {}
    if clean or not path.is_file():
        return entries
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(
            f"[docs] warning: ignoring unreadable {path.name}: {error}",
            file=sys.stderr,
        )
        return entries
    for item in raw.get("versions", []):
        if not isinstance(item, dict) or "version" not in item:
            continue
        try:
            entry = VersionEntry.from_json(item)
        except (KeyError, TypeError, ValueError):
            continue
        if (docs_root / entry.version).is_dir():
            entries[entry.version] = entry
    return entries


def write_versions(
    path: Path, entries: list[VersionEntry], latest: str, dry_run: bool
) -> None:
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest": latest,
        "versions": [entry.as_json() for entry in entries],
    }
    write_file(path, json.dumps(payload, indent=2) + "\n", dry_run)


def build_site(
    config: Config,
    output: Path,
    releases: list[Release],
    entries: dict[str, VersionEntry],
    latest: str,
    search_scope: str,
    dry_run: bool,
) -> int:
    """Render every release into ``site/docs``; returns the number of files."""
    docs_root = output / DOCS_DIR_NAME

    def search_for(version: str) -> bool:
        if search_scope == "none":
            return False
        return search_scope == "all" or version == latest

    unresolved: list[str] = []
    for release in releases:
        collect_pages(release, config)
        unresolved.extend(render_documents(release, config))

    for release in releases:
        entries[release.version] = VersionEntry.from_release(release)
    versions = sort_versions(list(entries.values()))

    written = 0
    for release in releases:
        enabled = search_for(release.version)
        for page in release.pages:
            document = render_page(page, release, config, versions, latest, enabled)
            write_file(docs_root / release.version / page.out, document, dry_run)
            written += 1
        hub = render_hub(
            release,
            config,
            versions,
            latest,
            page_dir=release.version,
            search_enabled=enabled,
        )
        write_file(docs_root / release.version / "index.html", hub, dry_run)
        written += 1
        if enabled:
            index = search_index(release, config)
            write_file(docs_root / release.version / "search.json", index, dry_run)
            written += 1

    if releases:
        newest = max(releases, key=lambda item: version_key(item.version))
        root_hub = render_hub(
            newest,
            config,
            versions,
            latest,
            page_dir="",
            search_enabled=search_for(newest.version),
        )
        write_file(docs_root / "index.html", root_hub, dry_run)
        written += 1

    written += len(write_assets(docs_root, dry_run))
    write_versions(docs_root / VERSIONS_FILE, versions, latest, dry_run)
    seen: set[str] = set()
    for problem in unresolved:
        if problem not in seen:
            seen.add(problem)
            print(f"[docs] warning: unresolved link in {problem}", file=sys.stderr)
    return written


def copy_landing(output: Path, dry_run: bool) -> bool:
    """Publish the landing page as the site root (single source: landing/)."""
    source = REPO_ROOT / "landing" / "index.html"
    if not source.exists():
        return False
    if not dry_run:
        output.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output / "index.html")
    return True


ATTR_RE = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')


def link_exists(output: Path, page: Path, target: str) -> bool:
    path_part = target.partition("#")[0].partition("?")[0]
    if not path_part:
        return True
    base = output if path_part.startswith("/") else page.parent
    cleaned = unquote(path_part.lstrip("/"))
    candidate = Path(os.path.normpath(str(base / cleaned)))
    return candidate.is_file() or (candidate / "index.html").is_file()


def check_links(output: Path) -> list[str]:
    """Crawl the generated HTML and report internal links with no target."""
    problems: list[str] = []
    for page in sorted(output.rglob("*.html")):
        name = page.relative_to(output).as_posix()
        for target in ATTR_RE.findall(page.read_text(encoding="utf-8")):
            if not target or target.startswith(
                ("#", "//", "mailto:", "tel:", "data:")
            ):
                continue
            if SCHEME_RE.match(target):
                continue
            if not link_exists(output, page, target):
                problems.append(f"{name} -> {target}")
    return problems


def serve(output: Path, port: int) -> None:
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    handler = partial(SimpleHTTPRequestHandler, directory=str(output))
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"[docs] serving {output} on http://127.0.0.1:{port}/docs/")
    print("[docs] press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


def resolve_output(value: Path) -> Path:
    return value if value.is_absolute() else (Path.cwd() / value).resolve()


def main(argv: list[str] | None = None) -> int:
    global SOURCE_ROOT
    parser = argparse.ArgumentParser(
        prog="build_docs.py",
        description=(
            "Generate the versioned /docs site from the Markdown files in the "
            "source repository (default: this repo)."
        ),
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "repository the docs are generated from (llm-router checkout); "
            f"falls back to ${SOURCE_ENV}, [site] source_repo, then this repo"
        ),
    )
    parser.add_argument(
        "--all-versions",
        action="store_true",
        help="build every release tag as well (default: only .version)",
    )
    parser.add_argument(
        "--include-prerelease",
        action="store_true",
        help="with --all-versions, also build -rc/-prod style tags",
    )
    parser.add_argument(
        "--max-versions", type=int, default=None, help="cap the number of releases"
    )
    parser.add_argument(
        "--clean", action="store_true", help="delete site/docs before building"
    )
    parser.add_argument(
        "--search",
        choices=("all", "latest", "none"),
        default="all",
        help="which versions get a search.json index",
    )
    parser.add_argument(
        "--check-links", action="store_true", help="fail on broken internal links"
    )
    parser.add_argument(
        "--serve", action="store_true", help="serve the build locally"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--dry-run", action="store_true", help="render, write nothing"
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="do not create .venv-docs when the markdown package is missing",
    )
    args = parser.parse_args(argv)

    if not args.no_bootstrap:
        bootstrap_dependencies(args.quiet)

    config = load_config(args.config)
    SOURCE_ROOT = resolve_source_root(args.source, config)
    output = resolve_output(args.output)
    docs_root = output / DOCS_DIR_NAME

    if args.clean and docs_root.exists():
        if not args.dry_run:
            shutil.rmtree(docs_root)
        entries: dict[str, VersionEntry] = {}
    else:
        entries = read_versions(docs_root / VERSIONS_FILE, docs_root, clean=False)

    limit = args.max_versions or (None if args.all_versions else 1)
    releases = collect_releases(args.include_prerelease, limit)
    if not any(release.source == "worktree" for release in releases):
        releases.insert(0, current_release())

    candidates = [release.version for release in releases] + list(entries)
    latest = max(candidates, key=version_key)

    written = build_site(
        config, output, releases, entries, latest, args.search, args.dry_run
    )
    landing = copy_landing(output, args.dry_run)

    if not args.quiet:
        prefix = "would write" if args.dry_run else "wrote"
        worktree = next(
            release for release in releases if release.source == "worktree"
        )
        print(
            f"[docs] source: {SOURCE_ROOT} "
            f"(v{worktree.version} from {worktree.ref})"
        )
        print(f"[docs] {prefix} {written} files into {output}")
        for release in releases:
            print(
                f"[docs]   v{release.version:<9} {len(release.pages):>3} pages "
                f"from {release.ref} ({release.source})"
            )
        print(f"[docs]   {len(entries):>16} versions indexed, latest is v{latest}")
        print(f"[docs] landing page: {'included' if landing else 'not found'}")

    status = 0
    if args.check_links:
        if args.dry_run:
            print(
                "[docs] warning: --check-links needs a real build", file=sys.stderr
            )
        else:
            problems = check_links(output)
            if problems:
                status = 1
                print(
                    f"[docs] {len(problems)} broken internal link(s):",
                    file=sys.stderr,
                )
                for problem in problems[:40]:
                    print(f"[docs]   {problem}", file=sys.stderr)
            else:
                print("[docs] internal links OK")

    if args.serve:
        serve(output, args.port)
    return status


if __name__ == "__main__":
    sys.exit(main())
