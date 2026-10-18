"""
Bezpieczne przetwarzanie i formatowanie Markdown oraz statystyk dla generowanych artykułów.
"""

import html
import re
from urllib.parse import urlparse


def split_headline(text: str) -> tuple[str | None, str]:
    """Wydziela pierwszy nagłówek najwyższego poziomu (# Tytuł) jako tytuł artykułu."""
    if not text:
        return None, ""

    lines = text.replace("\r\n", "\n").split("\n")
    for i in range(min(len(lines), 6)):
        match = re.match(r"^#\s+(.+?)\s*$", lines[i])
        if match:
            headline = match.group(1).strip()
            body = "\n".join(lines[:i] + [""] + lines[i + 1:])
            return headline, body

    return None, text


def _render_inline(text: str) -> str:
    """Bezpieczne renderowanie znaczników liniowych (**bold**, *italic*, `code`)."""
    escaped = html.escape(text)

    # `code`
    escaped = re.sub(
        r"`([^`]+)`",
        r'<code class="rounded bg-paper-200 px-1 py-0.5 font-mono text-[0.85em] text-accent-800">\1</code>',
        escaped,
    )

    # **strong**
    escaped = re.sub(
        r"\*\*([^*]+)\*\*",
        r'<strong class="font-semibold text-ink-950">\1</strong>',
        escaped,
    )

    # *em*
    escaped = re.sub(
        r"\*([^*]+)\*",
        r'<em class="italic">\1</em>',
        escaped,
    )

    return escaped


def render_markdown_html(text: str) -> str:
    """
    Bezpieczny, lekki parser Markdown renderujący HTML zgodny ze stylami artykułu.
    Chroni przed atakami XSS poprzez ucieczkę (html.escape) przed konwersją znaczników.
    """
    if not text:
        return ""

    lines = text.replace("\r\n", "\n").split("\n")
    output: list[str] = []

    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph():
        nonlocal paragraph
        if not paragraph:
            return
        content = " ".join(paragraph)
        output.append(f'<p class="mb-6">{_render_inline(content)}</p>')
        paragraph = []

    def flush_list():
        nonlocal list_items
        if not list_items:
            return
        ordered = all(re.match(r"^\d+[.)]\s+", item) for item in list_items)
        items_html = []
        for idx, item in enumerate(list_items):
            clean_item = re.sub(r"^(\*|-|\d+[.)])\s+", "", item)
            bullet = f"{idx + 1}." if ordered else "•"
            items_html.append(
                f'<li class="flex gap-3">'
                f'<span class="mt-[0.35em] shrink-0 font-sans text-sm font-semibold text-accent-700">{bullet}</span>'
                f'<span class="min-w-0 flex-1">{_render_inline(clean_item)}</span>'
                f'</li>'
            )
        output.append(
            f'<ul class="mb-7 space-y-3 border-l-2 border-accent-200 pl-5">{"".join(items_html)}</ul>'
        )
        list_items = []

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            flush_list()
            flush_paragraph()
            continue

        # Horizontal rule: ---, ***, ___
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line):
            flush_list()
            flush_paragraph()
            output.append(
                '<div class="my-10 flex justify-center gap-3 text-accent-600" aria-hidden="true">'
                '<span>✧</span><span>✧</span><span>✧</span>'
                '</div>'
            )
            continue

        # Headings: #..######
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading_match:
            flush_list()
            flush_paragraph()
            level = len(heading_match.group(1))
            heading_content = _render_inline(heading_match.group(2))
            if level <= 2:
                output.append(
                    f'<h3 class="mb-4 mt-12 text-[1.75rem] font-semibold leading-snug tracking-tight text-ink-950 sm:text-3xl">{heading_content}</h3>'
                )
            else:
                output.append(
                    f'<h4 class="mb-3 mt-9 text-xl font-semibold leading-snug text-ink-950 sm:text-2xl">{heading_content}</h4>'
                )
            continue

        # Lists: * item, - item, 1. item
        if re.match(r"^(\*|-|\d+[.)])\s+", line):
            flush_paragraph()
            list_items.append(line)
            continue

        paragraph.append(line)

    flush_list()
    flush_paragraph()

    return "\n".join(output)


def format_crawled_date(when_crawled: str | None) -> str:
    """Formatowanie '2026-10-13T08:15:30.123' -> '2026-10-13 08:15'."""
    if not when_crawled:
        return "—"
    return str(when_crawled).split(".")[0].replace("T", " ")


def format_when(value: str | int | float | None, fallback: str = "—") -> str:
    """Formatowanie timestampu."""
    if value is None or value == "":
        return fallback
    return str(value).split(".")[0].replace("T", " ")


def host_of(url: str | None) -> str:
    """Zwraca domenę / hostname z URL."""
    if not url:
        return "—"
    try:
        parsed = urlparse(url)
        return parsed.hostname or url
    except Exception:
        return url


def word_count(text: str | None) -> int:
    """Liczba słów w tekście."""
    if not text:
        return 0
    trimmed = text.strip()
    if not trimmed:
        return 0
    return len(trimmed.split())


def reading_minutes(text: str | None) -> int:
    """Szacowany czas czytania w minutach (180 słów / min)."""
    words = word_count(text)
    return max(1, round(words / 180))
