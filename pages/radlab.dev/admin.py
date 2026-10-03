#!/usr/bin/env python3
"""Okienko do zarządzania wpisami bloga radlab.dev.

Uruchomienie (Python z rozszerzeniem Tk, np. /usr/bin/python3):

    /usr/bin/python3 admin.py
    LLM_ROUTER_API=http://127.0.0.1:8080 /usr/bin/python3 admin.py

Funkcje: dodawanie, edycja i usuwanie wpisów (PL/EN) oraz tłumaczenie wpisu
na drugi język przez LLM Router (llm_router_lib). Tłumaczenie tworzy wersję
roboczą (draft) z skopiowanymi mediami i wpisem w config/translations.json.

Logika leży w admin_core.py; to plik jest wyłącznie warstwą GUI.
"""

from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import traceback
import webbrowser
from collections import OrderedDict
from datetime import date
from pathlib import Path
try:
    import tkinter
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Brak modułu tkinter — uruchom skrypt interpreterem z rozszerzeniem Tk,\n"
        "np.: /usr/bin/python3 admin.py\n"
    )
    raise
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from admin_core import (  # noqa: E402
    ContentStore,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_LANG,
    LANGS,
    LoadedPost,
    PostError,
    PostInfo,
    Translator,
    translate_post,
    today_iso,
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LANG_LABELS = {"pl": "PL", "en": "EN"}

MEDIA_FILETYPES = {
    "image": ("Obrazy", "*.png *.jpg *.jpeg *.webp *.gif *.svg *.avif *.heif *.heic"),
    "video": ("Filmy", "*.webm *.mp4 *.mov *.mkv *.avi"),
}

PREVIEW_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
PREVIEW_LINK_RE = re.compile(r"(?<![!\w])\[([^\]]+)\]\(([^)\s]+)\)")
PREVIEW_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
PREVIEW_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
PREVIEW_CODE_RE = re.compile(r"`([^`\n]+)`")


class WorkerResult:
    """Outcome of a background job, delivered to the Tk main loop."""

    def __init__(self, ok: bool, message: str = "", payload: object = None,
                 final: bool = True, show_error: bool = True,
                 progress_value: float | None = None, log: str | None = None):
        self.ok = ok
        self.message = message
        self.payload = payload
        self.final = final
        self.show_error = show_error
        self.progress_value = progress_value
        self.log = log


class AdminApp:
    def __init__(self, root: Tk):
        self.root = root
        self.store = ContentStore(ROOT)
        self.translator: Translator | None = None
        self.translator_lock = threading.Lock()
        self.jobs: queue.Queue[WorkerResult] = queue.Queue()
        self.busy = False
        self.current: LoadedPost | None = None   # loaded from disk
        self.current_slug: str | None = None     # slug as loaded (rename check)
        self._loaded_id: str | None = None       # "lang:slug" shown in the editor
        self.preview_links: list[tuple[tuple[int, int], tuple[int, int], str]] = []
        self.build_log_window: tkinter.Toplevel | None = None
        self._builder_python: str | None = None
        self._builder_python_checked = False
        self.models: list[str] = []

        root.title("RadLab — panel zarządzania blogiem")
        root.geometry("1280x820")
        self._build_ui()
        self.refresh_list(select=None)
        self.root.after(150, self._poll_jobs)
        self._start_router_probe()

    # ------------------------------------------------------------ ui layout

    def _build_ui(self) -> None:
        pad = {"padx": 6, "pady": 4}
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)

        toolbar = ttk.Frame(body)
        toolbar.pack(fill="x", **pad)
        self.btn_new = ttk.Button(toolbar, text="Nowy wpis…", command=self.on_new)
        self.btn_new.pack(side="left", padx=3)
        self.btn_save = ttk.Button(toolbar, text="Zapisz", command=self.on_save, state="disabled")
        self.btn_save.pack(side="left", padx=3)
        self.btn_delete = ttk.Button(toolbar, text="Usuń", command=self.on_delete, state="disabled")
        self.btn_delete.pack(side="left", padx=3)
        self.btn_translate = ttk.Button(toolbar, text="Tłumacz…", command=self.on_translate, state="disabled")
        self.btn_translate.pack(side="left", padx=3)
        self.btn_switch = ttk.Button(toolbar, text="Wersja ↔", command=self._open_counterpart, state="disabled")
        self.btn_switch.pack(side="left", padx=3)
        ttk.Button(toolbar, text="Odśwież",
                   command=lambda: self.refresh_list(select=self.selected())).pack(side="left", padx=3)
        self.btn_build = ttk.Button(toolbar, text="Buduj stronę…", command=self.on_build)
        self.btn_build.pack(side="left", padx=3)

        paned = ttk.PanedWindow(body, orient="horizontal")
        paned.pack(fill="both", expand=True, **pad)

        list_frame = ttk.LabelFrame(paned, text="Wpisy")
        paned.add(list_frame, weight=1)
        columns = ("date", "version", "status", "title")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        for key, text, width in (("date", "Data", 90), ("version", "Wersja", 50),
                                 ("status", "Status", 130), ("title", "Tytuł", 420)):
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor="w")
        self.tree.column("version", stretch=False)
        self.tree.column("status", stretch=False)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self.on_select())
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        editor = ttk.LabelFrame(paned, text="Edytor")
        paned.add(editor, weight=3)
        grid = ttk.Frame(editor)
        grid.pack(fill="both", expand=True, padx=8, pady=6)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        self.entry_title = self._field(grid, 0, 0, "Tytuł *")
        self.entry_date = self._field(grid, 0, 2, "Data *", width=12)
        self.entry_slug = self._field(grid, 1, 0, "Slug *")
        self.entry_desc = self._field(grid, 1, 2, "Opis (SEO)")
        self.entry_tags = self._field(grid, 2, 0, "Tagi (przecinki)")
        self.entry_cats = self._field(grid, 2, 2, "Kategorie (przecinki)")
        self.entry_image = self._field(grid, 3, 0, "Obraz (media/…)")
        flags_row = ttk.Frame(grid)
        flags_row.grid(row=3, column=2, sticky="w")
        self.chk_draft = ttk.Checkbutton(flags_row, text="wersja robocza (draft)")
        self.chk_draft.pack(side="left", padx=(0, 10))
        self.chk_updated = ttk.Checkbutton(flags_row, text="zapisz datę aktualizacji (dziś)")
        self.chk_updated.pack(side="left")
        self.chk_updated.state(["selected"])

        self.lbl_version = ttk.Label(grid, text="", foreground="#0b57d0", cursor="hand2")
        self.lbl_version.grid(row=4, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.lbl_version.bind("<Button-1>", lambda _e: self._open_counterpart())

        body_frame = ttk.LabelFrame(grid, text="Treść (Markdown)")
        body_frame.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(6, 0))
        grid.rowconfigure(5, weight=1)

        media_bar = ttk.Frame(body_frame)
        media_bar.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Button(media_bar, text="Wstaw obraz…",
                   command=lambda: self._insert_media("image")).pack(side="left", padx=3)
        ttk.Button(media_bar, text="Wstaw film…",
                   command=lambda: self._insert_media("video")).pack(side="left", padx=3)
        self.lbl_media_hint = ttk.Label(media_bar, text="plik jest kopiowany do media/ wpisu",
                                        foreground="#777")
        self.lbl_media_hint.pack(side="left", padx=8)

        self.notebook = ttk.Notebook(body_frame)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)
        editor_tab = ttk.Frame(self.notebook)
        preview_tab = ttk.Frame(self.notebook)
        self.notebook.add(editor_tab, text="  Edycja  ")
        self.notebook.add(preview_tab, text="  Podgląd  ")

        self.txt_body = tkinter.Text(editor_tab, wrap="none", undo=True,
                                     font=("monospace", 10))
        body_scroll = ttk.Scrollbar(editor_tab, orient="vertical", command=self.txt_body.yview)
        self.txt_body.configure(yscrollcommand=body_scroll.set)
        self.txt_body.pack(side="left", fill="both", expand=True)
        body_scroll.pack(side="right", fill="y")
        self.txt_body.bind("<Tab>", self._insert_tab)

        self.txt_preview = tkinter.Text(preview_tab, wrap="word", state="disabled",
                                        padx=10, pady=6, background="#fbfcfd")
        preview_scroll = ttk.Scrollbar(preview_tab, orient="vertical",
                                       command=self.txt_preview.yview)
        self.txt_preview.configure(yscrollcommand=preview_scroll.set)
        self.txt_preview.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")
        self._configure_preview_tags()
        self.txt_preview.bind("<Button-1>", self._on_preview_click)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.status_var = tkinter.StringVar(value="Gotowe")
        status = ttk.Label(body, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")
        self.progress = ttk.Progressbar(body, mode="determinate", maximum=100)
        self.progress.pack(fill="x", side="bottom")
        self._update_editor_buttons()

    def _field(self, parent: ttk.Frame, row: int, col: int, label: str,
               width: int | None = None) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=3)
        entry = ttk.Entry(parent)
        if width:
            entry.configure(width=width)
        entry.grid(row=row, column=col + 1, sticky="ew", pady=3)
        return entry

    def _insert_tab(self, _event) -> str:
        self.txt_body.insert("insert", "    ")
        return "break"

    # ------------------------------------------------------- preview (md)

    def _configure_preview_tags(self) -> None:
        pv = self.txt_preview
        pv.tag_configure("h1", font=("TkDefaultFont", 16, "bold"), spacing1=6, spacing3=4)
        pv.tag_configure("h2", font=("TkDefaultFont", 13, "bold"), spacing1=5, spacing3=3)
        pv.tag_configure("h3", font=("TkDefaultFont", 11, "bold"), spacing1=3)
        pv.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        pv.tag_configure("italic", font=("TkDefaultFont", 10, "italic"))
        pv.tag_configure("code", font=("monospace", 9), background="#eef0f3")
        pv.tag_configure("link", foreground="#0b57d0", underline=True)
        pv.tag_configure("image", foreground="#8a8f98", font=("TkDefaultFont", 9, "italic"))
        pv.tag_configure("quote", foreground="#555f6e", lmargin1=18, lmargin2=18)
        pv.tag_configure("list", lmargin1=18, lmargin2=28)
        pv.tag_configure("hr", foreground="#c3c8d0")

    def _on_tab_changed(self, _event) -> None:
        try:
            selected = self.notebook.tab(self.notebook.select(), "text").strip()
        except tkinter.TclError:
            return
        if selected == "Podgląd":
            self._render_preview()

    def _pv_tuple(self, index: str) -> tuple[int, int]:
        line, _, col = index.partition(".")
        return int(line), int(col)

    def _pv_insert(self, chunk: str, base_tag: str = "") -> None:
        if not chunk:
            return
        self.txt_preview.insert("end", chunk)
        if base_tag:
            end = self.txt_preview.index("end-1c")
            self.txt_preview.tag_add(base_tag, f"{end}-{len(chunk)}c", end)

    def _pv_placeholder(self, label: str, url: str | None) -> None:
        self.txt_preview.insert("end", label, "image")
        end = self.txt_preview.index("end-1c")
        if url and url.startswith("http"):
            start = self.txt_preview.index(f"end-{len(label)}c")
            self.txt_preview.tag_add("link", start, end)
            self.preview_links.append((self._pv_tuple(start), self._pv_tuple(end), url))

    def _pv_inline(self, line_text: str, base_tag: str = "") -> None:
        """Insert one line with inline Markdown styling (bold/italic/code/link/image)."""
        spans: list[tuple[int, int, str, str]] = []
        for regex, tag in ((PREVIEW_IMAGE_RE, "image"), (PREVIEW_LINK_RE, "link"),
                           (PREVIEW_BOLD_RE, "bold"), (PREVIEW_ITALIC_RE, "italic"),
                           (PREVIEW_CODE_RE, "code")):
            for match in regex.finditer(line_text):
                spans.append((match.start(), match.end(), tag, match.group(0)))
        spans.sort(key=lambda s: (s[0], s[1]))
        kept: list[tuple[int, int, str, str]] = []
        for span in spans:
            if kept and span[0] < kept[-1][1]:
                continue
            kept.append(span)
        cursor = 0
        for start, end, tag, raw_span in kept:
            if start > cursor:
                self._pv_insert(line_text[cursor:start], base_tag)
            if tag == "image":
                url = raw_span[raw_span.index("(") + 1:raw_span.rindex(")")]
                self._pv_placeholder(f"[obraz: {url}]", None)
            elif tag == "link":
                label = raw_span[1:raw_span.index("]")]
                url = raw_span[raw_span.index("(") + 1:raw_span.rindex(")")]
                self._pv_placeholder(label, url)
            else:
                inner = raw_span[2:-2] if tag == "bold" else raw_span[1:-1]
                self._pv_insert(inner, tag)
            cursor = end
        if cursor < len(line_text):
            self._pv_insert(line_text[cursor:], base_tag)

    def _render_preview(self) -> None:
        """Simplified Markdown preview: headings, lists, quotes, code, links,
        images/videos as placeholders. Not a full HTML render."""
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("1.0", "end")
        self.preview_links = []
        in_code = False
        for line in self.txt_body.get("1.0", "end-1c").splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
                self.txt_preview.insert("end", line + "\n", "code")
                continue
            if in_code:
                self.txt_preview.insert("end", (line or " ") + "\n", "code")
                continue
            if not line.strip():
                self.txt_preview.insert("end", "\n")
                continue
            heading = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading:
                level = min(len(heading.group(1)), 3)
                self._pv_inline(heading.group(2), f"h{level}")
                self.txt_preview.insert("end", "\n", f"h{level}")
                continue
            if re.match(r"^\s*(---+|\*\*\*+)\s*$", line):
                self.txt_preview.insert("end", "— " * 24 + "\n", "hr")
                continue
            if line.lstrip().startswith(">"):
                self._pv_inline(re.sub(r"^\s*>\s?", "", line), "quote")
                self.txt_preview.insert("end", "\n", "quote")
                continue
            list_item = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
            if list_item:
                self._pv_insert(f"{list_item.group(1)}  {list_item.group(2)} ", "list")
                self._pv_inline(list_item.group(3), "list")
                self.txt_preview.insert("end", "\n", "list")
                continue
            video = re.match(r"^\s*\{\{<\s*video\s+(\S+?)\s*>}}\s*$", line)
            if video:
                self._pv_placeholder(f"[film: {video.group(1)}]", None)
                self.txt_preview.insert("end", "\n")
                continue
            youtube = re.match(r"^\s*\{\{<\s*youtube\s+([\w-]{11})\s*>}}\s*$", line)
            if youtube:
                self._pv_placeholder("[YouTube]", f"https://www.youtube.com/watch?v={youtube.group(1)}")
                self.txt_preview.insert("end", "\n")
                continue
            self._pv_inline(line)
            self.txt_preview.insert("end", "\n")
        self.txt_preview.configure(state="disabled")

    def _on_preview_click(self, event) -> None:
        try:
            clicked = self._pv_tuple(self.txt_preview.index(f"@{event.x},{event.y}"))
        except tkinter.TclError:
            return
        for start, end, url in self.preview_links:
            if start <= clicked <= end:
                webbrowser.open(url)
                return

    # ------------------------------------------------------------- media

    def _insert_media(self, kind: str) -> None:
        """Pick a file from disk, copy it into the post's media/ dir and insert
        the Markdown snippet (image or {{< video >}} shortcode) at the cursor."""
        if self.busy or not self.current:
            return
        if self._is_dirty() and not self._save_current(silent=True):
            return
        post = self.current
        label, pattern = MEDIA_FILETYPES[kind]
        chosen = filedialog.askopenfilename(
            title=f"Wstaw do {post.lang}/{post.slug}",
            filetypes=[(label, pattern), ("Wszystkie pliki", "*.*")],
        )
        if not chosen:
            return
        source_path = Path(chosen)
        try:
            media_dir = self.store.post_dir(post.lang, post.slug) / "media"
            media_dir.mkdir(parents=True, exist_ok=True)
            dest_name = self._unique_media_name(media_dir, source_path.name)
            shutil.copy2(source_path, media_dir / dest_name)
        except OSError as exc:
            messagebox.showerror("RadLab", f"Nie udało się skopiować pliku:\n{exc}")
            return
        rel = f"media/{dest_name}"
        if kind == "image":
            self.txt_body.insert("insert", f"![{source_path.stem}]({rel})\n")
            if not self.entry_image.get().strip():
                self.entry_image.insert(0, rel)
        else:
            self.txt_body.insert("insert", "{{< video " + rel + " >}}\n")
        self.notebook.select(0)
        self.status_var.set(f"Wstawiono: {rel} (kopia w {post.lang}/{post.slug}/media/)")

    @staticmethod
    def _unique_media_name(directory: Path, filename: str) -> str:
        candidate = filename
        stem, suffix = Path(filename).stem, Path(filename).suffix
        number = 2
        while (directory / candidate).exists():
            candidate = f"{stem}-{number}{suffix}"
            number += 1
        return candidate

    # ------------------------------------------------------------- post list

    def selected(self) -> str | None:
        # item id is the "lang:slug" key set at insert time
        item = self.tree.selection()
        return item[0] if item else None

    def _group_key(self, lang: str, slug: str, translations: dict) -> str:
        """Article identity: the PL slug, or a synthetic key for EN-only posts."""
        if lang == DEFAULT_LANG:
            return slug
        return next((pl for pl, pair in translations.items()
                     if (pair or {}).get("en") == slug), f"en:{slug}")

    @staticmethod
    def _group_summary(pl: PostInfo | None, en: PostInfo | None) -> str:
        def mark(post: PostInfo | None) -> str:
            if post is None:
                return "—"
            return "draft" if post.draft else "✓"
        return f"PL {mark(pl)} · EN {mark(en)}"

    def refresh_list(self, select: str | None = None) -> None:
        translations = self.store.read_translations()
        groups: dict[str, list[PostInfo]] = {}
        for post in self.store.list_posts():
            key = self._group_key(post.lang, post.slug, translations)
            groups.setdefault(key, []).append(post)
        ordered = sorted(
            ((max(p.date for p in members), key, members) for key, members in groups.items()),
            key=lambda item: (item[0], item[1]), reverse=True,
        )
        self.tree.delete(*self.tree.get_children())
        for date, key, members in ordered:
            pl = next((p for p in members if p.lang == DEFAULT_LANG), None)
            en = next((p for p in members if p.lang != DEFAULT_LANG), None)
            parent_id = f"grp:{key}"
            self.tree.insert("", "end", id=parent_id,
                             values=(date, "", self._group_summary(pl, en),
                                     (pl or en).title),
                             tags=("group",))
            for post in sorted(members, key=lambda p: (p.lang != DEFAULT_LANG, p.slug)):
                status = "draft" if post.draft else "✓"
                child_id = f"{post.lang}:{post.slug}"
                self.tree.insert(parent_id, "end", id=child_id,
                                 values=(post.date, LANG_LABELS.get(post.lang, post.lang),
                                         status, post.title),
                                 tags=("draft",) if post.draft else ())
            self.tree.item(parent_id, open=True)
        self.tree.tag_configure("group", font=("TkDefaultFont", 10, "bold"))
        self.tree.tag_configure("draft", foreground="#8a6d00")
        if select:
            target = self._resolve_select(select)
            if target:
                self.tree.selection_set(target)
                self.tree.see(target)

    def _resolve_select(self, select: str) -> str | None:
        """Version id for a requested selection; a group id resolves to PL (or the only version)."""
        if not self.tree.exists(select):
            return None
        if not select.startswith("grp:"):
            return select
        children = self.tree.get_children(select)
        if not children:
            return None
        return next((child for child in children
                     if self.tree.set(child, "version") == LANG_LABELS[DEFAULT_LANG]),
                    children[0])

    def on_select(self) -> None:
        selection = self.selected()
        # re-selecting an already-loaded post would re-fire this event through
        # refresh_list() forever; the id guard breaks the loop
        if not selection or self.busy:
            return
        if selection.startswith("grp:"):
            target = self._resolve_select(selection)
            if not target:
                return
            selection = target
        if self._loaded_id == selection:
            return
        if self._confirm_discard():
            return
        lang, _, slug = selection.partition(":")
        try:
            self._load_into_editor(self.store.load_post(lang, slug))
            self.refresh_list(select=selection)
        except PostError as exc:
            messagebox.showerror("RadLab", str(exc))

    def _load_into_editor(self, post: LoadedPost) -> None:
        self.current = post
        self.current_slug = post.slug
        self._loaded_id = f"{post.lang}:{post.slug}" if post.slug else None
        meta = post.meta
        self.entry_title.delete(0, "end")
        self.entry_title.insert(0, str(meta.get("title", "")))
        self.entry_date.delete(0, "end")
        date_value = meta.get("date")
        if hasattr(date_value, "isoformat"):
            date_value = date_value.isoformat()
        self.entry_date.insert(0, str(date_value or today_iso())[:10])
        self.entry_slug.delete(0, "end")
        self.entry_slug.insert(0, str(meta.get("slug", post.slug)))
        self.entry_desc.delete(0, "end")
        self.entry_desc.insert(0, str(meta.get("description", "")))
        self.entry_tags.delete(0, "end")
        self.entry_tags.insert(0, ", ".join(str(t) for t in (meta.get("tags") or [])))
        self.entry_cats.delete(0, "end")
        self.entry_cats.insert(0, ", ".join(str(c) for c in (meta.get("categories") or [])))
        self.entry_image.delete(0, "end")
        self.entry_image.insert(0, str(meta.get("image", "")))
        if meta.get("draft"):
            self.chk_draft.state(["selected"])
        else:
            self.chk_draft.state(["!selected"])
        self.chk_updated.state(["selected"])
        self._update_version_label()
        self.txt_body.delete("1.0", "end")
        self.txt_body.insert("1.0", post.body)
        self._update_editor_buttons()

    def _update_editor_buttons(self) -> None:
        has_post = bool(self.current)
        state = "normal" if has_post and not self.busy else "disabled"
        self.btn_save.configure(state=state)
        self.btn_delete.configure(state=state)
        self.btn_translate.configure(state=state)
        self.btn_switch.configure(state=state)

    def _update_version_label(self) -> None:
        """Clickable line under the form: open the counterpart, or translate if missing."""
        if not self.current:
            self.lbl_version.configure(text="")
            return
        other = "en" if self.current.lang == DEFAULT_LANG else DEFAULT_LANG
        counterpart = self.store.find_counterpart(self.current.lang, self.current.slug)
        if not counterpart:
            self.lbl_version.configure(
                text=f"Brak wersji {other.upper()} — kliknij, aby przetłumaczyć",
                foreground="#8a6d00")
            return
        status = ""
        try:
            if self.store.load_post(other, counterpart).meta.get("draft"):
                status = " (draft)"
        except PostError:
            status = " (brak pliku!)"
        self.lbl_version.configure(
            text=f"Wersja {other.upper()}: {counterpart}{status} — kliknij, aby otworzyć",
            foreground="#0b57d0")

    def _open_counterpart(self) -> None:
        """Switch the editor to the other-language version; offer translation if missing."""
        if self.busy or not self.current:
            return
        counterpart = self.store.find_counterpart(self.current.lang, self.current.slug)
        if not counterpart:
            self.on_translate()
            return
        other = "en" if self.current.lang == DEFAULT_LANG else DEFAULT_LANG
        selection = f"{other}:{counterpart}"
        if self._loaded_id == selection:
            return
        if self._confirm_discard():
            return
        try:
            self._load_into_editor(self.store.load_post(other, counterpart))
            self.refresh_list(select=selection)
        except PostError as exc:
            messagebox.showerror("RadLab", str(exc))

    def _on_tree_double_click(self, _event) -> None:
        selection = self.selected()
        if not selection or selection.startswith("grp:") or self._loaded_id != selection:
            return
        self._open_counterpart()

    def _is_dirty(self) -> bool:
        if self.current is None:
            return False
        meta = self.current.meta
        meta_date = meta.get("date")
        if hasattr(meta_date, "isoformat"):
            meta_date = meta_date.isoformat()
        return (
            self.entry_title.get().strip() != str(meta.get("title", ""))
            or self.entry_date.get().strip()[:10] != str(meta_date or "")[:10]
            or self.entry_slug.get().strip() != str(meta.get("slug", self.current.slug))
            or self.entry_desc.get().strip() != str(meta.get("description", ""))
            or self.entry_tags.get().strip() != ", ".join(str(t) for t in (meta.get("tags") or []))
            or self.entry_cats.get().strip() != ", ".join(str(c) for c in (meta.get("categories") or []))
            or self.entry_image.get().strip() != str(meta.get("image", ""))
            or bool(self.chk_draft.instate(["selected"])) != bool(meta.get("draft", False))
            or self.txt_body.get("1.0", "end-1c") != self.current.body
        )

    def _confirm_discard(self) -> bool:
        """Ask before throwing away unsaved edits; True means abort the action."""
        if not self._is_dirty():
            return False
        answer = messagebox.askyesnocancel(
            "RadLab", "Masz niezapisane zmiany. Zapisać przed kontynuowaniem?")
        if answer is None:
            return True
        if answer:
            return not self._save_current(silent=True)
        return False

    # ------------------------------------------------------------------ CRUD

    def on_new(self) -> None:
        if self.busy:
            return
        if self._confirm_discard():
            return
        dlg = LanguageDialog(self.root)
        if dlg.run() is None:
            return
        lang = dlg.lang
        post = LoadedPost(
            lang=lang, slug="", body="", path=Path("."),
            meta=OrderedDict([
                ("title", ""), ("date", date.today()), ("slug", ""),
                ("lang", lang), ("draft", True),
            ]),
        )
        self._load_into_editor(post)
        self.refresh_list()
        self.status_var.set(f"Nowy wpis ({lang}) — uzupełnij pola i zapisz")
        self.entry_title.focus_set()

    def _collect_form(self) -> tuple[OrderedDict, str] | None:
        if self.current is None:
            return None
        title = self.entry_title.get().strip()
        date_text = self.entry_date.get().strip()
        slug = self.entry_slug.get().strip()
        if not title:
            messagebox.showerror("RadLab", "Podaj tytuł wpisu.")
            return None
        if not DATE_RE.match(date_text):
            messagebox.showerror("RadLab", "Data w formacie RRRR-MM-DD.")
            return None
        if not slug:
            slug = slugify_title(title)
            self.entry_slug.delete(0, "end")
            self.entry_slug.insert(0, slug)
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
            messagebox.showerror("RadLab", "Slug może zawierać małe litery, cyfry i myślniki.")
            return None
        meta: "OrderedDict[str, object]" = OrderedDict()
        # preserve keys we do not edit in the form (wp_id, translation_of)
        for key, value in self.current.meta.items():
            if key in ("wp_id", "translation_of"):
                meta[key] = value
        meta["title"] = title
        meta["date"] = date_text
        if self.chk_updated.instate(["selected"]):
            meta["updated"] = date.today()
        elif "updated" in self.current.meta:
            meta["updated"] = self.current.meta["updated"]
        # unchecked and never updated before: the field is left out
        meta["slug"] = slug
        description = self.entry_desc.get().strip()
        if description:
            meta["description"] = description
        tags = [t.strip() for t in self.entry_tags.get().split(",") if t.strip()]
        if tags:
            meta["tags"] = tags
        categories = [c.strip() for c in self.entry_cats.get().split(",") if c.strip()]
        if categories:
            meta["categories"] = categories
        image = self.entry_image.get().strip()
        if image:
            meta["image"] = image
        meta["lang"] = self.current.lang
        if self.chk_draft.instate(["selected"]):
            meta["draft"] = True
        body = self.txt_body.get("1.0", "end-1c")
        return meta, body

    def _save_current(self, silent: bool = False) -> bool:
        if not self.current:
            return False
        collected = self._collect_form()
        if collected is None:
            return False
        meta, body = collected
        lang = str(meta.get("lang", DEFAULT_LANG))
        new_slug = str(meta["slug"])
        try:
            if self.current_slug and new_slug != self.current_slug:
                if self.store.post_exists(lang, new_slug):
                    raise PostError(f"wpis {lang}/{new_slug} już istnieje")
                self.store.rename_post(lang, self.current_slug, new_slug)
            path = self.store.save_post(lang, new_slug, meta, body)
        except PostError as exc:
            messagebox.showerror("RadLab", str(exc))
            return False
        self.current = self.store.load_post(lang, new_slug)
        self.current_slug = new_slug
        self._loaded_id = f"{lang}:{new_slug}"
        self.refresh_list(select=f"{lang}:{new_slug}")
        if not silent:
            self.status_var.set(f"Zapisano: {path.relative_to(self.store.root)}")
        return True

    def on_save(self) -> None:
        if self.busy or not self.current:
            return
        self._save_current()

    def on_delete(self) -> None:
        if self.busy or not self.current:
            return
        if self._confirm_discard():
            return
        post = self.current
        if not messagebox.askyesno(
                "RadLab",
                f"Usunąć wpis {post.lang}/{post.slug} razem z katalogiem mediów?"):
            return
        try:
            self.store.delete_post(post.lang, post.slug)
        except PostError as exc:
            messagebox.showerror("RadLab", str(exc))
            return
        self._load_into_editor_empty()
        self.refresh_list()
        self.status_var.set(f"Usunięto: {post.lang}/{post.slug}")

    def _load_into_editor_empty(self) -> None:
        self.entry_title.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, today_iso())
        self.entry_slug.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.entry_tags.delete(0, "end")
        self.entry_cats.delete(0, "end")
        self.entry_image.delete(0, "end")
        self.chk_draft.state(["selected"])
        self.chk_updated.state(["selected"])
        self.txt_body.delete("1.0", "end")
        self.current = None
        self.current_slug = None
        self._loaded_id = None
        self._update_version_label()
        self._update_editor_buttons()

    # ------------------------------------------------------------ translation

    def _start_router_probe(self) -> None:
        self.status_var.set("Łączenie z LLM Routerem…")
        self._spawn(self._job_probe)

    def _job_probe(self) -> WorkerResult:
        try:
            translator = self._ensure_translator()
            models = translator.list_models()
            self.models = models
            return WorkerResult(True, f"LLM Router: {translator.api} ({len(models)} modeli)")
        except Exception as exc:  # noqa: BLE001 — router down is not fatal for CRUD
            return WorkerResult(
                False,
                f"LLM Router niedostępny ({exc.__class__.__name__}) — tłumaczenie będzie dostępne po restarcie routera",
                show_error=False,
            )

    def _ensure_translator(self) -> Translator:
        with self.translator_lock:
            if self.translator is None:
                self.translator = Translator(model=None)
            return self.translator

    def on_translate(self) -> None:
        if self.busy or not self.current:
            return
        source = self.current
        target_lang = "en" if source.lang == "pl" else "pl"
        counterpart = self.store.find_counterpart(source.lang, source.slug)
        dlg = TranslateDialog(self.root, source, target_lang, self.models, counterpart)
        if dlg.run() is None:
            return
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._spawn(self._job_translate, dlg)

    def _job_translate(self, options) -> WorkerResult:
        try:
            translator = self._ensure_translator()

            def progress(done: int, total: int, label: str) -> None:
                self.jobs.put(WorkerResult(
                    True, f"Tłumaczę: {label} ({done}/{total})",
                    final=False, show_error=False,
                    progress_value=int(done / total * 100)))

            loaded = translate_post(
                self.store, options.source_lang, options.source_slug,
                options.target_lang, translator,
                model=options.model, make_draft=options.make_draft,
                max_new_tokens=options.max_new_tokens, overwrite=options.overwrite,
                progress=progress,
            )
            return WorkerResult(
                True,
                f"Przetłumaczono na {options.target_lang.upper()}: {loaded.slug} "
                f"(wersja robocza, do weryfikacji)",
                payload=(options.target_lang, loaded.slug),
            )
        except PostError as exc:
            return WorkerResult(False, str(exc))
        except Exception as exc:  # noqa: BLE001 — surface any router failure
            return WorkerResult(False, f"Błąd tłumaczenia: {exc}")

    # ----------------------------------------------------------------- build

    def _find_builder_python(self) -> str | None:
        """An interpreter with the build.py dependencies (cached after first check)."""
        if self._builder_python_checked:
            return self._builder_python
        self._builder_python_checked = True
        candidates = [os.environ.get("BUILDER_PYTHON"), sys.executable,
                      "/usr/local/bin/python3",
                      "/mnt/data2/dev/develop/python-venv/bin/python3.10"]
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                probe = subprocess.run(
                    [candidate, "-c", "import markdown, jinja2, markupsafe, pygments, yaml, PIL"],
                    capture_output=True, timeout=20)
            except (OSError, subprocess.SubprocessError):
                continue
            if probe.returncode == 0:
                self._builder_python = candidate
                return candidate
        return None

    @staticmethod
    def _parse_stage(line: str) -> float | None:
        """build.py prints '[n/5] stage' — map it to a 0-100 bar value."""
        match = re.match(r"^\[(\d+)/5\]", line)
        if match:
            return int(match.group(1)) / 5 * 100
        if line.startswith("built "):
            return 100
        return None

    def _build_log_alive(self) -> bool:
        return (self.build_log_window is not None
                and self.build_log_window.winfo_exists())

    def _open_build_log_window(self) -> None:
        if self._build_log_alive():
            self.build_log_window.deiconify()
            self.build_log_text.delete("1.0", "end")
            self.build_log_progress.configure(value=0)
            self.build_log_status.configure(text="Start…")
            return
        win = tkinter.Toplevel(self.root)
        win.title("Budowanie strony — logi")
        win.transient(self.root)
        win.geometry("780x480")
        win.minsize(560, 320)
        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.build_log_text = tkinter.Text(frame, state="disabled", wrap="none",
                                           font=("monospace", 9))
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.build_log_text.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.build_log_text.xview)
        self.build_log_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.build_log_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        bar_frame = ttk.Frame(win)
        bar_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.build_log_progress = ttk.Progressbar(bar_frame, mode="determinate", maximum=100)
        self.build_log_progress.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.build_log_status = ttk.Label(bar_frame, text="Start…")
        self.build_log_status.pack(side="left")
        buttons = ttk.Frame(win)
        buttons.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(buttons, text="Kopiuj log", command=self._copy_build_log).pack(side="left")
        ttk.Button(buttons, text="Zamknij", command=win.destroy).pack(side="right")
        self.build_log_window = win

    def _append_build_log(self, line: str) -> None:
        if not self._build_log_alive():
            return
        self.build_log_text.configure(state="normal")
        self.build_log_text.insert("end", line + "\n")
        self.build_log_text.see("end")
        self.build_log_text.configure(state="disabled")

    def _copy_build_log(self) -> None:
        if not self._build_log_alive():
            return
        self.build_log_window.clipboard_clear()
        self.build_log_window.clipboard_append(self.build_log_text.get("1.0", "end-1c"))

    def on_build(self) -> None:
        if self.busy:
            return
        if self._confirm_discard():
            return
        dlg = BuildDialog(self.root)
        if dlg.run() is None:
            return
        self._open_build_log_window()
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._spawn(self._job_build, dlg)

    def _job_build(self, options) -> WorkerResult:
        python = self._find_builder_python()
        if not python:
            return WorkerResult(
                False,
                "Brak interpretera z zależnościami build.py "
                "(markdown, jinja2, pygments, PIL) — ustaw BUILDER_PYTHON.")
        cmd = [python, str(ROOT / "build.py")]
        if options.fast:
            cmd.append("--fast")
        if options.drafts:
            cmd.append("--drafts")
        if options.check:
            cmd.append("--check")
        if options.clean:
            cmd.append("--clean")
        self.jobs.put(WorkerResult(True, "Budowanie…", final=False,
                                   log="$ " + " ".join(cmd)))
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, cwd=str(ROOT), bufsize=1)
        except OSError as exc:
            return WorkerResult(False, f"Nie udało się uruchomić budowania: {exc}")
        for line in proc.stdout:
            line = line.rstrip("\n")
            self.jobs.put(WorkerResult(True, line, final=False, log=line,
                                       progress_value=self._parse_stage(line)))
        rc = proc.wait()
        if rc == 0:
            return WorkerResult(True, "Budowanie zakończone pomyślnie → dist/")
        return WorkerResult(False, f"Budowanie zakończone kodem {rc} — szczegóły w logach")

    # -------------------------------------------------------------- threading

    def _spawn(self, func, *args) -> None:
        self.busy = True
        self.btn_new.configure(state="disabled")
        self.btn_build.configure(state="disabled")
        self._update_editor_buttons()

        def runner() -> None:
            try:
                result = func(*args)
            except Exception as exc:  # noqa: BLE001
                result = WorkerResult(False, f"Błąd: {exc}\n{traceback.format_exc()}")
            self.jobs.put(result)

        threading.Thread(target=runner, daemon=True).start()

    def _poll_jobs(self) -> None:
        finished = None
        try:
            while True:
                result = self.jobs.get_nowait()
                if result.message:
                    self.status_var.set(result.message)
                if result.log is not None:
                    self._append_build_log(result.log)
                if result.progress_value is not None:
                    if str(self.progress.cget("mode")) == "indeterminate":
                        self.progress.stop()
                        self.progress.configure(mode="determinate")
                    self.progress.configure(value=result.progress_value)
                    if self._build_log_alive():
                        self.build_log_progress.configure(value=result.progress_value)
                if not result.final:
                    continue
                if result.payload is not None:
                    lang, slug = result.payload
                    self._load_into_editor(self.store.load_post(lang, slug))
                    self.refresh_list(select=f"{lang}:{slug}")
                if str(self.progress.cget("mode")) == "indeterminate":
                    self.progress.stop()
                self.progress.configure(mode="determinate", value=0)
                finished = result
        except queue.Empty:
            pass
        if finished is not None:
            self.busy = False
            self.btn_new.configure(state="normal")
            self.btn_build.configure(state="normal")
            self._update_editor_buttons()
            if self._build_log_alive():
                self.build_log_status.configure(text=finished.message or ("ok" if finished.ok else "błąd"))
            if not finished.ok and finished.show_error:
                messagebox.showerror("RadLab", finished.message or "Błąd")
        self.root.after(150, self._poll_jobs)

    def on_closing(self) -> None:
        if self.translator is not None:
            try:
                self.translator.close()
            except Exception:
                pass
        self.root.destroy()


def slugify_title(title: str) -> str:
    from admin_core import slugify
    return slugify(title)


class LanguageDialog:
    def __init__(self, parent):
        self.lang: str | None = None
        self.window = tkinter.Toplevel(parent)
        self.window.title("Nowy wpis")
        self.window.transient(parent)
        ttk.Label(self.window, text="Język wpisu:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.var = tkinter.StringVar(value=DEFAULT_LANG)
        for code in LANGS:
            ttk.Radiobutton(self.window, text=f"{code.upper()} ({code})",
                            value=code, variable=self.var).grid(
                row=0, column=1, sticky="w", padx=4, pady=2)
        ttk.Button(self.window, text="OK", command=self._ok).grid(row=1, column=0, pady=8)
        ttk.Button(self.window, text="Anuluj", command=self.window.destroy).grid(row=1, column=1, pady=8)

    def _ok(self) -> None:
        self.lang = self.var.get()
        self.window.destroy()

    def run(self) -> "LanguageDialog | None":
        self.window.grab_set()
        self.window.wait_window()
        return self if self.lang is not None else None


class TranslateDialog:
    def __init__(self, parent, source: LoadedPost, target_lang: str,
                 models: list[str], counterpart: str | None):
        self.source_lang = source.lang
        self.source_slug = source.slug
        self.target_lang = target_lang
        self.model: str | None = None
        self.make_draft = True
        self.overwrite = False
        self.max_new_tokens = DEFAULT_MAX_NEW_TOKENS

        self.window = tkinter.Toplevel(parent)
        self.window.title("Tłumaczenie wpisu")
        self.window.transient(parent)
        self.window.resizable(False, False)
        grid = ttk.Frame(self.window)
        grid.pack(fill="both", expand=True, padx=12, pady=10)
        grid.columnconfigure(1, weight=1)

        ttk.Label(grid, text=f"Źródło: {source.lang.upper()}/{source.slug}").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(grid, text=f"Cel: {target_lang.upper()}").grid(row=1, column=0, sticky="w")

        ttk.Label(grid, text="Model:").grid(row=2, column=0, sticky="w", pady=4)
        self.model_var = tkinter.StringVar()
        if models:
            self.model_var.set(models[0])
        self.model_box = ttk.Combobox(grid, textvariable=self.model_var, width=42,
                                      values=models)
        self.model_box.grid(row=2, column=1, sticky="ew", pady=4)
        if not models:
            ttk.Label(grid, text="(router niedostępny — podaj nazwę modelu ręcznie)",
                      foreground="#888").grid(row=3, column=1, sticky="w")

        ttk.Label(grid, text="Maks. tokeny (treść):").grid(row=4, column=0, sticky="w", pady=4)
        self.tokens_var = tkinter.StringVar(value=str(DEFAULT_MAX_NEW_TOKENS))
        ttk.Entry(grid, textvariable=self.tokens_var, width=12).grid(row=4, column=1, sticky="w", pady=4)

        self.draft_var = tkinter.BooleanVar(value=True)
        ttk.Checkbutton(grid, text="utwórz jako wersję roboczą (draft)",
                        variable=self.draft_var).grid(row=5, column=0, columnspan=2, sticky="w")
        overwrite_row = ttk.Frame(grid)
        overwrite_row.grid(row=6, column=0, columnspan=2, sticky="w")
        self.overwrite_var = tkinter.BooleanVar(value=False)
        self.overwrite_box = ttk.Checkbutton(
            overwrite_row,
            text="nadpisz istniejące tłumaczenie" if counterpart
            else "nadpisz (brak istniejącego tłumaczenia)",
            variable=self.overwrite_var)
        self.overwrite_box.pack(side="left")
        if counterpart:
            ttk.Label(overwrite_row, text=f"(obecne: {counterpart})",
                      foreground="#888").pack(side="left", padx=6)

        buttons = ttk.Frame(grid)
        buttons.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(buttons, text="Tłumacz", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Anuluj", command=self.window.destroy).pack(side="left", padx=4)

    def _ok(self) -> None:
        model = self.model_var.get().strip()
        if not model:
            messagebox.showerror("Tłumaczenie", "Podaj model.")
            return
        try:
            tokens = int(self.tokens_var.get().strip())
            if tokens <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Tłumaczenie", "Liczba tokenów musi być dodatnią liczbą.")
            return
        self.model = model
        self.max_new_tokens = tokens
        self.make_draft = bool(self.draft_var.get())
        self.overwrite = bool(self.overwrite_var.get())
        self.window.destroy()

    def run(self) -> "TranslateDialog | None":
        self.window.grab_set()
        self.window.wait_window()
        return self


class BuildDialog:
    def __init__(self, parent):
        self.fast = False
        self.drafts = False
        self.check = False
        self.clean = False

        self.window = tkinter.Toplevel(parent)
        self.window.title("Budowanie strony")
        self.window.transient(parent)
        self.window.resizable(False, False)
        grid = ttk.Frame(self.window)
        grid.pack(fill="both", expand=True, padx=12, pady=10)
        grid.columnconfigure(0, weight=1)

        ttk.Label(grid, text="Opcje (python build.py):").grid(
            row=0, column=0, sticky="w", pady=(0, 6))
        self.fast_var = tkinter.BooleanVar(value=False)
        ttk.Checkbutton(grid, text="szybkie budowanie (--fast) — bez generowania wariantów obrazów",
                        variable=self.fast_var).grid(row=1, column=0, sticky="w")
        self.drafts_var = tkinter.BooleanVar(value=False)
        ttk.Checkbutton(grid, text="wersje robocze (--drafts) — włączaj posty draft",
                        variable=self.drafts_var).grid(row=2, column=0, sticky="w", pady=2)
        self.check_var = tkinter.BooleanVar(value=False)
        ttk.Checkbutton(grid, text="walidacja (--check) — sprawdź linki i zasoby",
                        variable=self.check_var).grid(row=3, column=0, sticky="w")
        self.clean_var = tkinter.BooleanVar(value=False)
        ttk.Checkbutton(grid, text="wyczyść dist/ (--clean) — usuń poprzedni wynik",
                        variable=self.clean_var).grid(row=4, column=0, sticky="w", pady=(2, 8))

        buttons = ttk.Frame(grid)
        buttons.grid(row=5, column=0, sticky="w")
        ttk.Button(buttons, text="Buduj", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Anuluj", command=self.window.destroy).pack(side="left", padx=4)

    def _ok(self) -> None:
        self.fast = bool(self.fast_var.get())
        self.drafts = bool(self.drafts_var.get())
        self.check = bool(self.check_var.get())
        self.clean = bool(self.clean_var.get())
        self.window.destroy()

    def run(self) -> "BuildDialog | None":
        self.window.grab_set()
        self.window.wait_window()
        return self


def main() -> None:
    root = Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = AdminApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
