"""Convert a WordPress post body (rendered HTML) to Markdown.

The REST API will not hand back the original Markdown -- ``content.raw`` needs
admin rights and Gutenberg comments are stripped from ``content.rendered`` -- so
the source of truth here is the rendered DOM plus the ``wp-block-*`` classes.

Deliberately hand-rolled instead of using html2text: this corpus needs specific
policies that a generic converter gets wrong. Images have to resolve to a local
original rather than the served avif derivative, lightbox wrappers have to be
unwrapped while keeping a genuine link, ``<br>`` inside ``<pre>`` has to become a
real newline, ``<strong>`` inside ``<code>`` has to be dropped, and the code
blocks carry no language class at all so one has to be inferred.

Every conversion that loses information is recorded on the returned Report so a
migration run can be reviewed instead of trusted.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

# Placeholder the builder resolves to a built asset path plus srcset. Keeping a
# token instead of a relative path means the same Markdown body works from pl/
# and en/ alike and does not depend on output depth.
MEDIA_TOKEN = "@media"

YOUTUBE = re.compile(r"(?:youtube\.com/embed/|youtu\.be/)([\w-]{11})")
CODE_HINTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("json", re.compile(r'^\s*[{[][\s\S]*["\d\[]{1}', re.M)),
    ("bash", re.compile(r"^\s*(\$ |>> |#{1,2} |pip |curl |python\d? |docker |kubectl |git |apt |cd |ls |echo )", re.M)),
    ("python", re.compile(r"^\s*(from \w+ import |import \w+|def \w+\(|class \w+[\(:]|with open\(|self\.\w+)", re.M)),
    ("diff", re.compile(r"^\s*[-+]{2} ", re.M)),
)


@dataclass
class Report:
    """Things a conversion did that a human should look at, plus the asset map."""

    slug: str
    notes: list[str] = field(default_factory=list)
    images_missing_alt: list[str] = field(default_factory=list)
    images_unresolved: list[str] = field(default_factory=list)
    code_language_guesses: list[tuple[str, str]] = field(default_factory=list)
    # served URL -> repo-relative asset path, from data/media_map.json
    resolve: object = None

    def note(self, text: str) -> None:
        self.notes.append(text)

    def asset(self, url: str) -> str:
        """Rewrite a served image URL to the @media token the builder expands.

        Falls back to the remote URL, recorded as unresolved, so a missing
        download surfaces in the migration report instead of as a 404 later.
        """
        if self.resolve is None:
            return url
        entry = self.resolve(url)
        if entry is None:
            self.images_unresolved.append(url)
            return url
        return f"{MEDIA_TOKEN}/{Path(entry['local']).relative_to('media')}"


def infer_language(code: str) -> tuple[str, bool]:
    """Return (language, confident). Unconfident blocks are marked as plain text
    on purpose: a shell transcript highlighted as Python reads as authoritative
    and wrong, which is worse than no colouring."""
    for name, pattern in CODE_HINTS:
        if pattern.search(code):
            return name, True
    return "text", False


def _text(node) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    return "".join(_text(child) for child in getattr(node, "children", []))


def _inline(node, report: Report) -> str:
    """Inline markdown for a node.

    Siblings are accumulated so an emphasis node can see what was emitted just
    before it; adjacent markers such as ``*ang.***B**`` are unreadable and have
    to be caught while the text is being built, not patched afterwards.
    """
    if isinstance(node, NavigableString):
        return _escape(str(node))
    if not isinstance(node, Tag):
        return ""

    parts: list[str] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(_escape(str(child)))
        elif isinstance(child, Tag):
            parts.append(_inline_tag(child, "".join(parts), report))
    return "".join(parts)


def _inline_tag(node: Tag, emitted: str, report: Report) -> str:
    name = node.name.lower()
    inner = _inline(node, report)

    if name == "br":
        return "\n"
    if name in ("strong", "b"):
        return _emphasise("strong", inner, emitted)
    if name in ("em", "i"):
        return _emphasise("em", inner, emitted)
    if name == "code":
        content = node.get_text()
        return f"`{content}`" if content.strip() else ""
    if name == "a":
        href = node.get("href", "")
        if not href or href == "#":
            return inner
        return f"[{inner}]({href})"
    if name == "img":
        return _image(node, report)
    return inner


def _emphasise(kind: str, inner: str, emitted: str) -> str:
    """Wrap text in emphasis, keeping surrounding spaces outside the markers.

    WordPress writes <em>ang. </em><strong>B</strong> with the separating space
    inside the tag. Trimming it without putting it back glues the markers into
    ``*ang.***B**``, which no Markdown parser reads as intended. Where markers
    still collide, inline HTML is used: it renders identically and is never
    ambiguous.
    """
    lead = inner[: len(inner) - len(inner.lstrip())]
    trail = inner[len(inner.rstrip()):]
    core = inner.strip()
    if not core:
        return inner

    marker = "**" if kind == "strong" else "*"
    collides = (emitted.endswith("*") or core.startswith("*") or core.endswith("*"))
    if collides:
        return f"{lead}<{kind}>{core}</{kind}>{trail}"
    return f"{lead}{marker}{core}{marker}{trail}"


def _escape(text: str) -> str:
    # Only the characters that would silently create markdown syntax.
    return re.sub(r"(?<!\\)([*_`\[\]])", r"\\\1", text)


def _image(tag, report: Report) -> str:
    alt = (tag.get("alt") or "").strip()
    src = tag.get("src") or ""
    if not alt:
        report.images_missing_alt.append(src)
    return f"![{alt}]({report.asset(src)})"


def _code_block(tag, report: Report) -> str:
    """<pre> -> fenced block. WordPress puts newlines in <pre> as <br> inside
    <code> and leaves stray <strong>/&#91; entities behind."""
    code_tag = tag.find("code")
    source = code_tag if code_tag is not None else tag

    clone = BeautifulSoup(str(source), "html.parser")
    for br in clone.find_all("br"):
        br.replace_with("\n")
    for strong in clone.find_all(["strong", "b", "em", "i", "span", "a"]):
        strong.replace_with(strong.get_text())
    raw = html.unescape(clone.get_text())

    # A leading newline straight after <pre> is markup, not content.
    raw = re.sub(r"^\n", "", raw)
    raw = raw.rstrip()

    language = ""
    for cls in (code_tag.get("class", []) if code_tag else []) + tag.get("class", []):
        match = re.match(r"language-(\w+)", cls)
        if match:
            language = "python" if match.group(1) in ("py", "python3") else match.group(1)
    if not language:
        language, confident = infer_language(raw)
        language = language if confident else "text"
        report.code_language_guesses.append((language, raw.splitlines()[0][:60] if raw else ""))

    fence = "````" if "```" in raw else "```"
    return f"{fence}{language}\n{raw}\n{fence}"


def _figure(tag, report: Report) -> str:
    """<figure class="wp-block-image"> -> image, keeping the caption and a real
    link. The lightbox wrapper is dropped: it wrapped the image in an <a> to the
    full-size file, and that link is worth keeping even though the JS is gone."""
    img = tag.find("img")
    if img is None:
        inner = tag.find(["iframe", "video", "object"])
        if inner is not None:
            return _embed(inner, report)
        return _convert_children(tag, report)

    src = img.get("src", "")
    anchor = tag.find("a", href=True)
    link = anchor["href"] if anchor else None
    if link and _same_image(link, src):
        link = None  # the lightbox target, not a real destination

    markdown = _image(img, report)
    if link:
        markdown = f"[{markdown}]({link})"

    caption = tag.find("figcaption")
    if caption:
        return f"{markdown}\n\n_{_text(caption).strip()}_"
    return markdown


def _same_image(link: str, src: str) -> bool:
    """True when a link just points at another size of the same picture."""
    def stem(url: str) -> str:
        base = url.split("?")[0].rsplit("/", 1)[-1].lower()
        base = re.sub(r"-\d+x\d+(?=\.\w+$)", "", base)
        return re.sub(r"-(?:png|jpe?g|gif|webp|avif)$", "", base.rsplit(".", 1)[0])
    return bool(link) and stem(link) == stem(src)


def _embed(tag, report: Report) -> str:
    if tag.name == "iframe":
        match = YOUTUBE.search(tag.get("src", ""))
        if match:
            return "{{< youtube %s >}}" % match.group(1)
        report.note(f"dropped iframe {tag.get('src', '')[:80]}")
        return ""
    if tag.name == "video":
        return "{{< video %s >}}" % (tag.get("src") or "")
    if tag.name == "object":
        url = tag.get("data", "")
        return "[Pobierz PDF](%s)" % url if url else ""
    return ""


def _table(tag, report: Report) -> str:
    rows = [[cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
            for row in tag.find_all("tr")]
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    for row in rows:
        for index, cell in enumerate(row):
            row[index] = cell.replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(rows[0]) + " |",
           "| " + " | ".join("---" for _ in range(width)) + " |"]
    out += ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join(out)


def _list(tag, report: Report, depth: int = 0) -> str:
    lines: list[str] = []
    for index, item in enumerate(tag.find_all("li", recursive=False), start=1):
        bullet = f"{index}. " if tag.name == "ol" else "- "
        nested = [child for child in item.find_all(["ul", "ol"], recursive=False)]
        for child in nested:
            child.extract()
        text = " ".join(_inline(child, report) for child in item.children).strip()
        text = re.sub(r"\s+", " ", text)
        lines.append("    " * depth + bullet + text)
        for child in nested:
            lines.append(_list(child, report, depth + 1))
    return "\n".join(lines)


def _details(tag, report: Report) -> str:
    summary = tag.find("summary")
    title = summary.get_text(strip=True) if summary else "Szczegóły"
    if summary:
        summary.extract()
    body = _convert_children(tag, report).strip()
    return "{{< details title=\"%s\" >}}\n\n%s\n\n{{< /details >}}" % (title, body)


def _block_tag_to_markdown(text: str, level: int) -> str:
    """Legacy posts hard-code blockquotes as <p><strong>...</strong></p>; leave
    them alone but normalise the heading level used for section titles."""
    prefix = "#" * level
    return f"{prefix} {text.strip()}"


def _convert_children(tag, report: Report) -> str:
    blocks: list[str] = []
    for child in tag.children:
        rendered = _convert_block(child, report)
        if rendered.strip():
            blocks.append(rendered)
    return "\n\n".join(blocks)


def _convert_block(node, report: Report) -> str:
    if isinstance(node, NavigableString):
        text = str(node).strip()
        return _escape(text)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()

    if name in ("script", "style", "noscript", "form", "input", "button"):
        return ""

    if name == "figure":
        return _figure(node, report)
    if name == "img":
        return _image(node, report=report)
    if name == "pre":
        return _code_block(node, report)
    if name == "table":
        return _table(node, report)
    if name in ("ul", "ol"):
        return _list(node, report)
    if name == "details":
        return _details(node, report)
    if name in ("iframe", "video", "object"):
        return _embed(node, report)
    if name == "hr":
        return "---"
    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return _block_tag_to_markdown(_inline(node, report), int(name[1]))
    if name == "blockquote":
        cite = node.find("cite")
        body = _convert_children(node, report).strip()
        if cite:
            # "UWAGA!" callouts are pullquote + cite in this corpus.
            cite_text = cite.get_text(strip=True)
            if re.search(r"\bUWAGA\b", body, re.I):
                return f"{{{{< callout >}}}}\n\n{body}\n\n{cite_text}\n\n{{{{< /callout >}}}}"
            return f"> {body}\n>\n> — {cite_text}"
        quoted = "\n".join(f"> {line}" if line else ">" for line in body.splitlines())
        return quoted
    if name in ("p", "div", "section", "article", "main", "span"):
        if name == "p" and not node.find(["p", "div", "ul", "ol", "figure", "pre", "table"]):
            text = _inline(node, report).strip()
            # WP wraps bare inline content in <p class="wp-block-paragraph">
            return text
        return _convert_children(node, report)

    return _convert_children(node, report)


def normalise_headings(markdown: str) -> tuple[str, int]:
    """Posts from 2020-2024 use <h3> for section titles and no <h2> at all. A
    document whose sections start at h3 has a broken outline, so when there is
    no h2 anywhere we promote h3 -> h2 (and h4 -> h3) once."""
    if re.search(r"^##\s", markdown, re.M):
        return markdown, 0
    promoted = re.sub(r"^###(?=\s)", "##", markdown, flags=re.M)
    promoted = re.sub(r"^####(?=\s)", "###", promoted, flags=re.M)
    if promoted == markdown:
        return markdown, 0
    return promoted, len(re.findall(r"^##\s", promoted, re.M))


def convert(html_body: str, slug: str, *, resolve=None) -> tuple[str, Report]:
    """HTML body -> (markdown, report). ``resolve`` maps a served image URL to a
    media_map entry; without it images keep their remote URL and are reported."""
    report = Report(slug=slug, resolve=resolve)
    soup = BeautifulSoup(html_body, "html.parser")
    wrapper = soup.find("div", class_="entry-content") or soup
    markdown = _convert_children(wrapper, report)

    markdown, promoted = normalise_headings(markdown)
    if promoted:
        report.note(f"promoted {promoted} h3 section headings to h2")

    # Collapse runs of blank lines and stray empty paragraphs.
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n", report
