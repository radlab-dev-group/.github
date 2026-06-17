#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DSS 2026 AI Edition - Tutorial: Augmentacja danych z LLM, HITL i Active Learning.

Czysty, prosty i czytelny szablon nawiązujący do brandu DSS 2026 AI Edition
(czcionki Play / Arial, akcent cyan #00BEFE, ciemny fiolet #1B0532, granat #042733),
bez powielania grafiki brandowej. Treść na podstawie presentation/md.

Budżet: ~60 min prezentacji.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ----------------------------------------------------------------------------
# BRAND (DSS 2026 AI Edition) — paleta minimalna
# ----------------------------------------------------------------------------
INK = RGBColor(0x1B, 0x05, 0x32)   # ciemny fiolet — tekst główny
CYAN = RGBColor(0x00, 0xBE, 0xFE)   # akcent (linie, nagłówki tabel)
NAVY = RGBColor(0x04, 0x27, 0x33)   # tło slajdów tytułowych/sekcji
PURPLE = RGBColor(0x8B, 0x19, 0xFE)  # drugorzędny akcent
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x6B, 0x64, 0x78)   # tekst drugorzędny
LIGHT = RGBColor(0xF2, 0xF1, 0xF6)  # delikatne wypełnienie
CODE_BG = RGBColor(0x11, 0x0A, 0x22)
OK = RGBColor(0x1F, 0x9E, 0x55)
WARN = RGBColor(0xC9, 0x7A, 0x00)

TITLE_FONT = "Play"
BODY_FONT = "Arial"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.84)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]

_page = 0


# ----------------------------------------------------------------------------
# Helpery
# ----------------------------------------------------------------------------
def _bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def rect(slide, l, t, w, h, color, line=None, lw=Pt(1), rounded=False):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, l, t, w, h)
    shp.shadow.inherit = False
    if color is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = lw
    return shp


def tb(slide, l, t, w, h, runs, size=16, color=INK, bold=False, italic=False,
       font=BODY_FONT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0):
    """runs: str lub lista paragrafów; paragraf = str albo lista (text, dict-overrides)."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        segments = para if isinstance(para, list) else [(para, {})]
        if isinstance(para, str):
            segments = [(para, {})]
        for text, ov in segments:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(ov.get("size", size))
            r.font.color.rgb = ov.get("color", color)
            r.font.bold = ov.get("bold", bold)
            r.font.italic = ov.get("italic", italic)
            r.font.name = ov.get("font", font)
    return box


def bullets(slide, l, t, w, h, items, size=16, color=INK, gap=6, marker="▸  "):
    """items: (text, level) lub text. level 0/1."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        text, lvl = (it if isinstance(it, tuple) else (it, 0))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.05
        r = p.add_run()
        if lvl == 0:
            r.text = marker + text
            r.font.size = Pt(size)
            r.font.color.rgb = color
        else:
            r.text = "–  " + text
            r.font.size = Pt(size - 2)
            r.font.color.rgb = GRAY
            p.level = 1
        r.font.name = BODY_FONT
    return box


def footer(slide, section):
    global _page
    rect(slide, 0, Inches(7.04), SLIDE_W, Pt(1.2), LIGHT)
    tb(slide, MARGIN, Inches(7.08), Inches(9), Inches(0.32),
       "DSS 2026 AI Edition  ·  " + section, size=9, color=GRAY)
    tb(slide, Inches(11.6), Inches(7.08), Inches(0.9), Inches(0.32),
       str(_page), size=9, color=GRAY, align=PP_ALIGN.RIGHT)


def content(section, title, subtitle=None):
    """Slajd treściowy: biały, tytuł Play, linia cyan, stopka. Zwraca (slide, y_top)."""
    global _page
    _page += 1
    s = prs.slides.add_slide(BLANK)
    _bg(s, WHITE)
    tb(s, MARGIN, Inches(0.46), Inches(11.6), Inches(0.8), title,
       size=29, color=INK, bold=False, font=TITLE_FONT)
    rect(s, MARGIN, Inches(1.28), Inches(1.5), Pt(3.5), CYAN)
    y = Inches(1.55)
    if subtitle:
        tb(s, MARGIN, Inches(1.42), Inches(11.6), Inches(0.5), subtitle,
           size=15, color=GRAY, italic=True)
        y = Inches(2.0)
    footer(s, section)
    return s, y


def code_block(slide, l, t, w, lines, fs=12.5):
    h = Inches(0.18) + Inches(0.255) * len(lines)
    rect(slide, l, t, w, h, CODE_BG, rounded=True)
    box = slide.shapes.add_textbox(l + Inches(0.18), t + Inches(0.09),
                                   w - Inches(0.36), h - Inches(0.18))
    tf = box.text_frame
    tf.word_wrap = False
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(fs)
        r.font.name = "Consolas"
        r.font.color.rgb = CYAN if ln.strip().startswith("#") else RGBColor(0xE8, 0xE6, 0xF0)
    return t + h


def table(slide, l, t, w, headers, rows, col_w=None, fs=12, header_fs=12.5,
          row_h=Inches(0.34)):
    nrows = len(rows) + 1
    ncols = len(headers)
    h = row_h * nrows
    gtbl = slide.shapes.add_table(nrows, ncols, l, t, w, h).table
    gtbl.first_row = False
    gtbl.horz_banding = False
    if col_w:
        for i, cw in enumerate(col_w):
            gtbl.columns[i].width = cw
    # header
    for c, head in enumerate(headers):
        cell = gtbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.margin_top = Pt(2); cell.margin_bottom = Pt(2)
        cell.margin_left = Pt(6); cell.margin_right = Pt(6)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = head
        r.font.size = Pt(header_fs); r.font.bold = True
        r.font.color.rgb = CYAN; r.font.name = BODY_FONT
    # body
    for ri, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = gtbl.cell(ri, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if ri % 2 else LIGHT
            cell.margin_top = Pt(1); cell.margin_bottom = Pt(1)
            cell.margin_left = Pt(6); cell.margin_right = Pt(6)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(val)
            r.font.size = Pt(fs); r.font.color.rgb = INK
            r.font.name = BODY_FONT
            r.font.bold = (c == 0)
    return t + h


def callout(slide, l, t, w, h, text, accent=CYAN, icon="", title=None):
    rect(slide, l, t, w, h, LIGHT, rounded=True)
    rect(slide, l, t, Pt(4), h, accent)
    inner = l + Inches(0.28)
    body = []
    if title:
        body.append([((icon + "  " if icon else "") + title, {"bold": True, "color": INK, "size": 14})])
    body.append([(text, {"color": GRAY, "size": 13})])
    tb(slide, inner, t + Inches(0.12), w - Inches(0.5), h - Inches(0.2), body,
       anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)


# ----------------------------------------------------------------------------
# Slajdy tytułowe / sekcyjne
# ----------------------------------------------------------------------------
def cover():
    global _page
    _page += 1
    s = prs.slides.add_slide(BLANK)
    _bg(s, NAVY)
    rect(s, 0, Inches(2.55), Inches(2.0), Pt(5), CYAN)
    tb(s, MARGIN, Inches(0.95), Inches(2.5), Inches(0.4),
       "DSS 2026  ·  AI EDITION", size=14, color=CYAN, bold=True, font=BODY_FONT)
    tb(s, MARGIN, Inches(2.75), Inches(11.4), Inches(1.9),
       [[("Augmentacja danych z LLM,", {})], [("HITL i Active Learning", {})]],
       size=46, color=WHITE, font=TITLE_FONT, line_spacing=1.05)
    tb(s, MARGIN, Inches(4.75), Inches(11.0), Inches(0.7),
       "Od teorii do praktyki — kompletny proces wytwarzania modeli klasyfikacyjnych "
       "z wykorzystaniem lokalnych modeli generatywnych.",
       size=18, color=RGBColor(0xC9, 0xE9, 0xF5), font=BODY_FONT, line_spacing=1.15)
    tb(s, MARGIN, Inches(6.15), Inches(8), Inches(0.4),
       "Radlab Developer Services", size=16, color=CYAN, bold=True, font=BODY_FONT)
    tb(s, MARGIN, Inches(6.55), Inches(11), Inches(0.4),
       "Tutorial · ~60 min prezentacji + sesja pytań · interaktywna sesja anotacyjna",
       size=13, color=GRAY, font=BODY_FONT)


def section(num, title, time_label):
    global _page
    _page += 1
    s = prs.slides.add_slide(BLANK)
    _bg(s, NAVY)
    tb(s, MARGIN, Inches(2.45), Inches(2), Inches(0.7), f"{num:02d}",
       size=64, color=PURPLE, bold=True, font=TITLE_FONT)
    rect(s, MARGIN, Inches(3.55), Inches(2.0), Pt(4), CYAN)
    tb(s, MARGIN, Inches(3.75), Inches(11.4), Inches(1.2), title,
       size=40, color=WHITE, font=TITLE_FONT, line_spacing=1.05)
    tb(s, MARGIN, Inches(5.2), Inches(8), Inches(0.4), time_label,
       size=16, color=CYAN, font=BODY_FONT)


def closing():
    global _page
    _page += 1
    s = prs.slides.add_slide(BLANK)
    _bg(s, NAVY)
    rect(s, 0, Inches(2.85), Inches(2.0), Pt(5), CYAN)
    tb(s, MARGIN, Inches(3.05), Inches(11.4), Inches(1.1), "Dziękujemy!",
       size=54, color=WHITE, font=TITLE_FONT)
    tb(s, MARGIN, Inches(4.35), Inches(11), Inches(0.6),
       "Pytania i dyskusja — zachęcamy do anotacji na żywo.",
       size=20, color=RGBColor(0xC9, 0xE9, 0xF5), font=BODY_FONT)
    tb(s, MARGIN, Inches(5.2), Inches(11), Inches(0.4),
       "https://dss2026.radlab.dev/", size=18, color=CYAN, bold=True, font=BODY_FONT)
    tb(s, MARGIN, Inches(6.4), Inches(8), Inches(0.4),
       "Radlab Developer Services · DSS 2026 AI Edition",
       size=13, color=GRAY, font=BODY_FONT)


# ============================================================================
# BUDOWA DECKU (~60 min)
# ============================================================================

# --- 1. COVER (0:00) ---
cover()

# --- 2. AGENDA (0:30) ---
s, y = content("Agenda", "Agenda tutorialu")
agenda = [
    ("1", "Wstęp", "Czego dotyczy tutorial i jaka korzyść dla uczestników", "~2 min", PURPLE),
    ("2", "Część teoretyczno-praktyczna", "Augmentacja, labelowanie, klasyfikacja vs generowanie, HITL + AL, pętla", "~25 min", CYAN),
    ("★", "Anotacja na żywo", "Interaktywna sesja: dss2026.radlab.dev", "~5 min", PURPLE),
    ("3", "Część techniczna", "Sprzęt, vendorzy, LLM Router, labelowanie i augmentacja narzędziami, trening", "~22 min", CYAN),
    ("4", "Podsumowanie i wnioski", "Ocena modelu w W&B, wnioski i kierunki dalsze", "~6 min", PURPLE),
]
ay = y
for num, ttl, desc, tm, col in agenda:
    rect(s, MARGIN, ay, Inches(11.6), Inches(0.86), LIGHT, rounded=True)
    c = slide_circle = s.shapes.add_shape(MSO_SHAPE.OVAL, MARGIN + Inches(0.2), ay + Inches(0.18), Inches(0.5), Inches(0.5))
    c.shadow.inherit = False
    c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background()
    tb(s, MARGIN + Inches(0.2), ay + Inches(0.2), Inches(0.5), Inches(0.45), num,
       size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=TITLE_FONT)
    tb(s, MARGIN + Inches(0.95), ay + Inches(0.1), Inches(7.0), Inches(0.4), ttl,
       size=16, color=INK, bold=True)
    tb(s, MARGIN + Inches(0.95), ay + Inches(0.46), Inches(8.5), Inches(0.35), desc,
       size=12, color=GRAY)
    tb(s, MARGIN + Inches(9.6), ay, Inches(1.9), Inches(0.86), tm,
       size=14, color=col, bold=True, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    ay += Inches(1.02)

# --- 3. WSTĘP (2:00) ---
s, y = content("Wstęp", "Po co ten tutorial?")
tb(s, MARGIN, y, Inches(11.6), Inches(0.9),
   "Zaprezentujemy proces kontrolowanej augmentacji danych — od podstawowych pojęć po "
   "kompletny pipeline z udziałem człowieka w pętli (HITL) i Active Learningu (AL).",
   size=17, color=INK, line_spacing=1.2)
bullets(s, MARGIN, y + Inches(1.1), Inches(6.0), Inches(3.6), [
    "Labelowanie — człowiek vs LLM",
    "Augmentacja — nowe przykłady treningowe",
    "Klasyfikacja — modele decyzyjne",
    "Generowanie — LLM tworzy dane",
    "HITL + AL — człowiek w pętli uczenia aktywnego",
], size=17, gap=10)
callout(s, Inches(7.2), y + Inches(1.1), Inches(5.3), Inches(2.6),
        "Skrócenie czasu wytwarzania modeli klasyfikacyjnych oraz wsparcie w sytuacjach, "
        "gdy trudno zorganizować reprezentatywny zespół anotatorów.",
        accent=PURPLE, icon="◆", title="Cel i korzyść")
tb(s, Inches(7.2), y + Inches(3.9), Inches(5.3), Inches(0.6),
   "W trakcie: 5-minutowa sesja anotacyjna z udziałem uczestników.",
   size=13, color=GRAY, italic=True)

# === SEKCJA 1 ===
section(1, "Część teoretyczno-praktyczna", "~25 min · podstawy pojęciowe i metoda")

# --- AUGMENTACJA: definicja + cele ---
s, y = content("Teoria · Augmentacja", "Augmentacja danych",
               "Tworzenie nowych przykładów treningowych na bazie istniejącego zbioru")
tb(s, MARGIN, y, Inches(5.6), Inches(0.4), "Dobra augmentacja zapewnia, że przykłady:",
   size=15, color=INK, bold=True)
bullets(s, MARGIN, y + Inches(0.5), Inches(5.8), Inches(3.5), [
    "są zgodne z problemem",
    "zachowują poprawną etykietę",
    "zwiększają różnorodność zbioru",
    "pomagają modelowi generalizować",
    "uzupełniają klasy słabo reprezentowane",
], size=16, gap=9)
tb(s, Inches(7.0), y, Inches(5.5), Inches(0.4), "Metody dla tekstu:",
   size=15, color=INK, bold=True)
bullets(s, Inches(7.0), y + Inches(0.5), Inches(5.5), Inches(3.5), [
    "parafrazowanie przykładów",
    "zmiana stylu / długości wypowiedzi",
    "warianty formalne i nieformalne",
    "literówki, slang, język potoczny",
    "przykłady rzadkie i graniczne",
], size=16, gap=9)
callout(s, MARGIN, y + Inches(3.55), Inches(11.65), Inches(0.95),
        "„Chcę zwrócić produkt…” [zwrot]  →  „Jak odesłać towar?” · „Czy da się zrobić zwrot?” — "
        "wszystkie warianty pozostają w tej samej klasie.",
        accent=CYAN, icon="▸", title="Przykład (etykieta zachowana)")

# --- LABELOWANIE LLM ---
s, y = content("Teoria · Labelowanie", "Labelowanie danych z wykorzystaniem LLM",
               "Przypisywanie etykiet przykładom — klasyczne (człowiek) vs wspierane LLM")
tb(s, MARGIN, y, Inches(5.8), Inches(0.4), "Szczególnie przydatne, gdy:",
   size=15, color=INK, bold=True)
bullets(s, MARGIN, y + Inches(0.5), Inches(5.9), Inches(3.4), [
    "mamy dużo nieoznaczonych danych",
    "chcemy szybko pierwszy zbiór treningowy",
    "potrzebne wstępne etykiety do eksperymentów",
    "chcemy ograniczyć koszt ręcznej anotacji",
    "klasy da się jasno zdefiniować w promptach",
], size=15, gap=8)
callout(s, Inches(7.0), y, Inches(5.5), Inches(1.7),
        "Etykiety LLM to tylko propozycje. Model myli się przy ironii, niejednoznaczności, "
        "braku kontekstu i slangu.",
        accent=WARN, icon="⚠", title="Uwaga")
callout(s, Inches(7.0), y + Inches(1.9), Inches(5.5), Inches(1.65),
        "LLM nie zastępuje człowieka — przyspiesza etykietowanie. Człowiek kontroluje jakość, "
        "poprawia błędy i rozstrzyga trudne przypadki.",
        accent=OK, icon="✓", title="Zasada")

# --- KLASYFIKACJA vs GENEROWANIE ---
s, y = content("Teoria · Modele", "Klasyfikacja vs generowanie")
cardw = Inches(5.75)
rect(s, MARGIN, y, cardw, Inches(3.9), WHITE, line=CYAN, lw=Pt(1.5), rounded=True)
rect(s, MARGIN, y, cardw, Inches(0.6), NAVY, rounded=True)
tb(s, MARGIN, y + Inches(0.06), cardw, Inches(0.5), "MODEL KLASYFIKACYJNY",
   size=15, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
for i, (lab, val) in enumerate([
    ("Wejście", "„Nie mogę zalogować się do konta”"),
    ("Wyjście", "klasa: problem_logowania"),
    ("Dodatkowo", "prawdopodobieństwa klas + thresholdy"),
    ("Pytanie", "Do której kategorii należy przykład?"),
    ("Zalety", "szybki, tani, łatwy do wdrożenia"),
]):
    yy = y + Inches(0.8) + Inches(0.58) * i
    tb(s, MARGIN + Inches(0.25), yy, Inches(1.55), Inches(0.5), lab, size=12, color=PURPLE, bold=True)
    tb(s, MARGIN + Inches(1.75), yy, Inches(3.8), Inches(0.5), val, size=12.5, color=INK, line_spacing=1.0)
rx = Inches(7.0)
rect(s, rx, y, cardw, Inches(3.9), WHITE, line=PURPLE, lw=Pt(1.5), rounded=True)
rect(s, rx, y, cardw, Inches(0.6), NAVY, rounded=True)
tb(s, rx, y + Inches(0.06), cardw, Inches(0.5), "MODEL GENERATYWNY",
   size=15, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
for i, (lab, val) in enumerate([
    ("Wejście", "prompt: „Wygeneruj alternatywy zdania”"),
    ("Wyjście", "nowe teksty (warianty)"),
    ("Rola", "pomocnicza — przygotowuje dane"),
    ("Pytanie", "Co można wygenerować z kontekstu?"),
    ("Uwaga", "nie jest modelem docelowym"),
]):
    yy = y + Inches(0.8) + Inches(0.58) * i
    tb(s, rx + Inches(0.25), yy, Inches(1.55), Inches(0.5), lab, size=12, color=PURPLE, bold=True)
    tb(s, rx + Inches(1.75), yy, Inches(3.8), Inches(0.5), val, size=12.5, color=INK, line_spacing=1.0)
callout(s, MARGIN, y + Inches(4.05), Inches(11.65), Inches(0.65),
        "LLM generatywny przygotowuje dane → model klasyfikacyjny uczy się na nich podejmować decyzje.",
        accent=CYAN, icon="➜", title=None)

# --- ACTIVE LEARNING ---
s, y = content("Teoria · Active Learning", "Active Learning (AL)",
               "Pętla zwrotna: zamiast losowo, wybieramy najbardziej informacyjne przykłady")
tb(s, MARGIN, y, Inches(5.9), Inches(0.4), "AL wybiera przykłady, dla których model:",
   size=15, color=INK, bold=True)
bullets(s, MARGIN, y + Inches(0.5), Inches(6.0), Inches(3.4), [
    "ma niską pewność predykcji",
    "myli się między podobnymi klasami",
    "daje wysokie p-stwo dla kilku klas naraz",
    "jest niezgodny z inną regułą / modelem",
    "reprezentuje rzadką / problematyczną część danych",
], size=15, gap=8)
callout(s, Inches(7.05), y, Inches(5.45), Inches(2.3),
        "„Nie dostałem produktu i chcę pieniądze z powrotem”\n"
        "zwrot 0.42 · reklamacja 0.39 · status_dostawy 0.15\n"
        "Trudny przykład — poprawne oznaczenie uczy rozróżniania klas granicznych.",
        accent=PURPLE, icon="◎", title="Przykład trudnego przypadku")

# --- AL w kontekście augmentacji ---
s, y = content("Teoria · Active Learning", "Które dane warto augmentować?",
               "Nie zawsze cały zbiór po równo — liczebność klasy to nie wszystko")
bullets(s, MARGIN, y, Inches(5.9), Inches(3.6), [
    "klasy o najgorszych wynikach modelu",
    "przykłady z pogranicza kilku klas",
    "przypadki ważne biznesowo (wskazane przez człowieka)",
    "przykłady o niskiej pewności modelu",
    "nietypowe warianty językowe, slang, błędy",
], size=15, gap=8)
tb(s, Inches(7.0), y - Inches(0.1), Inches(5.5), Inches(0.4), "Proces kontrolowany:",
   size=14, color=INK, bold=True)
code_block(s, Inches(7.0), y + Inches(0.35), Inches(5.5), [
    "1. Trenuj prosty klasyfikator",
    "2. Sprawdź, gdzie się myli",
    "3. Zidentyfikuj klasy problematyczne",
    "4. Wygeneruj przykłady (LLM)",
    "5. Walidacja (człowiek / reguły)",
    "6. Trenuj ponownie",
    "7. Porównaj wyniki",
], fs=12.5)

# --- HITL ---
s, y = content("Teoria · HITL", "Human In The Loop (HITL)",
               "Człowiek jako świadoma część procesu uczenia i walidacji")
roles = [
    ("Definiuje reguły", "jakie klasy istnieją, co oznaczają, gdzie biegnie granica między nimi"),
    ("Sprawdza jakość", "czy przykład pasuje do etykiety, jest realistyczny, nie powiela oryginału"),
    ("Rozstrzyga niejasne", "spójne decyzje dla przypadków granicznych („koordynator”)"),
    ("Kontroluje uczenie", "metryki, confusion matrix, klasy rzadkie, jakość języka"),
]
for i, (ttl, desc) in enumerate(roles):
    col = MARGIN if i % 2 == 0 else Inches(7.0)
    row = y + (Inches(0) if i < 2 else Inches(1.9))
    rect(s, col, row, Inches(5.5), Inches(1.6), LIGHT, rounded=True)
    rect(s, col, row, Pt(4), Inches(1.6), CYAN)
    tb(s, col + Inches(0.3), row + Inches(0.18), Inches(5.0), Inches(0.4), ttl,
       size=16, color=INK, bold=True)
    tb(s, col + Inches(0.3), row + Inches(0.65), Inches(5.0), Inches(0.85), desc,
       size=13, color=GRAY, line_spacing=1.1)

# --- PĘTLA ---
s, y = content("Teoria · Pętla", "Pętla HITL z wykorzystaniem AL")
qs = [("Augmentacja", "Jak zwiększyć i urozmaicić zbiór?", CYAN),
      ("Active Learning", "Które dane są warte uwagi?", PURPLE),
      ("Human in the Loop", "Jak utrzymać jakość i kontrolę?", CYAN)]
for i, (q, a, c) in enumerate(qs):
    x = MARGIN + Inches(3.95) * i
    rect(s, x, y, Inches(3.7), Inches(1.3), LIGHT, rounded=True)
    rect(s, x, y, Inches(3.7), Inches(0.5), c, rounded=True)
    tb(s, x, y + Inches(0.07), Inches(3.7), Inches(0.4), q, size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    tb(s, x + Inches(0.2), y + Inches(0.65), Inches(3.3), Inches(0.6), a, size=13, color=INK, align=PP_ALIGN.CENTER)
flow = ["Zbiór danych", "Trening", "Analiza błędów", "Wybór do augmentacji",
        "Generowanie (LLM)", "Walidacja", "Aktualizacja", "Ponowny trening"]
fy = y + Inches(1.75)
tb(s, MARGIN, fy, Inches(11.6), Inches(0.35), "Przepływ:", size=14, color=INK, bold=True)
for i, f in enumerate(flow):
    x = MARGIN + Inches(1.46) * i
    rect(s, x, fy + Inches(0.5), Inches(1.32), Inches(0.7), NAVY, rounded=True)
    tb(s, x + Inches(0.04), fy + Inches(0.5), Inches(1.24), Inches(0.7), f,
       size=9.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < len(flow) - 1:
        tb(s, x + Inches(1.3), fy + Inches(0.5), Inches(0.18), Inches(0.7), "›",
           size=16, color=CYAN, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
callout(s, MARGIN, fy + Inches(1.5), Inches(11.65), Inches(0.75),
        "Bezpieczniejsza niż „weź dane → wygeneruj 10× więcej → trenuj”. Samo zwiększenie liczby "
        "przykładów nie gwarantuje poprawy — może nawet pogorszyć wynik.",
        accent=WARN, icon="⚠", title=None)

# --- ANOTACJA LIVE ---
global_section = "Sesja na żywo"
_page += 1
s = prs.slides.add_slide(BLANK)
_bg(s, NAVY)
rect(s, MARGIN, Inches(1.7), Inches(2.0), Pt(4), CYAN)
tb(s, MARGIN, Inches(1.9), Inches(11.4), Inches(0.9), "Interaktywna sesja anotacyjna",
   size=38, color=WHITE, font=TITLE_FONT)
tb(s, MARGIN, Inches(2.95), Inches(11.0), Inches(0.6),
   "Spróbuj sam — przekonaj się, jak trudno dokładnie oznaczać tekst bez kontekstu biznesowego.",
   size=18, color=RGBColor(0xC9, 0xE9, 0xF5))
rect(s, MARGIN, Inches(3.9), Inches(7.0), Inches(1.1), CYAN, rounded=True)
tb(s, MARGIN, Inches(4.05), Inches(7.0), Inches(0.4), "Link do sesji (~5 min):",
   size=13, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
tb(s, MARGIN, Inches(4.42), Inches(7.0), Inches(0.5), "https://dss2026.radlab.dev/",
   size=24, color=NAVY, bold=True, align=PP_ALIGN.CENTER, font=TITLE_FONT)
for i, (t1, t2) in enumerate([("Przeczytaj", "każdy tweet uważnie"),
                              ("Zastanów się", "jaka jest intencja"),
                              ("Wybierz", "najlepszą klasę"),
                              ("Zwróć uwagę", "na niuanse i kontekst")]):
    x = MARGIN + Inches(2.95) * i
    tb(s, x, Inches(5.6), Inches(2.8), Inches(0.4), t1, size=15, color=CYAN, bold=True)
    tb(s, x, Inches(6.0), Inches(2.8), Inches(0.4), t2, size=13, color=RGBColor(0xC9, 0xE9, 0xF5))

# === SEKCJA 3 (techniczna) ===
section(3, "Część techniczna", "~22 min · od sprzętu po trening klasyfikatora")

# --- SPRZĘT ---
s, y = content("Technika · Sprzęt", "Wymagania sprzętowe")
table(s, MARGIN, y, Inches(11.65),
      ["Komponent", "Minimalne", "Zalecane", "Uwagi"],
      [["CPU", "4 rdzenie", "8+ rdzeni", "batch wielowątkowy: więcej rdzeni = szybciej"],
       ["RAM", "16 GB", "32–128 GB+", "7B: 16GB · 70B: 64GB+ · 120B: 96GB+"],
       ["Dysk", "50 GB", "250 GB+", "Bielik ~5GB · PLLuM ~40GB · gpt-oss ~65GB"],
       ["GPU", "opcjonalne", "24–80 GB VRAM", "Bielik 8GB · PLLuM 48GB+ · gpt-oss 80GB"],
       ["System", "Linux / macOS 13+", "Ubuntu 22.04+", "Linux docelowy; vLLM tylko Linux+NVIDIA"]],
      col_w=[Inches(1.7), Inches(2.2), Inches(2.4), Inches(5.35)], fs=12, row_h=Inches(0.5))
callout(s, MARGIN, y + Inches(3.35), Inches(11.65), Inches(0.75),
        "Wymagania zależą od modelu i vendora. Bez GPU używaj Ollama / llama.cpp (CPU-only). "
        "Python 3.10+ (zalecane 3.12+), izolowany venv, zależności z requirements.txt.",
        accent=CYAN, icon="ℹ", title=None)

# --- VENDORZY przegląd + porównanie ---
s, y = content("Technika · Vendorzy", "Lokalne silniki (vendorzy)",
               "Trzy sposoby serwowania modeli lokalnie")
for i, (name, desc, col) in enumerate([
    ("vLLM", "wysokowydajny, GPU NVIDIA, tensor parallelism, multi-GPU", CYAN),
    ("Ollama", "najprostszy, GGUF, NVIDIA/AMD/Apple/CPU, API :11434", PURPLE),
    ("llama.cpp", "lekki C/C++, GGUF, największa kontrola, najwięcej konfiguracji", CYAN)]):
    yy = y + Inches(0.78) * i
    rect(s, MARGIN, yy, Inches(11.65), Inches(0.66), LIGHT, rounded=True)
    rect(s, MARGIN, yy, Inches(1.7), Inches(0.66), col, rounded=True)
    tb(s, MARGIN, yy + Inches(0.12), Inches(1.7), Inches(0.4), name, size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    tb(s, MARGIN + Inches(1.95), yy, Inches(9.4), Inches(0.66), desc, size=13.5, color=INK, anchor=MSO_ANCHOR.MIDDLE)
table(s, MARGIN, y + Inches(2.6), Inches(11.65),
      ["Cecha", "vLLM", "Ollama", "llama.cpp"],
      [["GPU", "NVIDIA (CUDA)", "ROCm/Metal/CUDA", "CUDA/Metal/Vulkan"],
       ["CPU-only / macOS / Win", "✗ / ✗ / ✗", "✓ / ✓ / WSL2", "✓ / ✓ / ✓"],
       ["Łatwość konfiguracji", "średnia", "łatwa", "trudna"],
       ["Wydajność GPU / CPU", "b. wysoka / brak", "wysoka / dobra", "wysoka / b. dobra"],
       ["Modele 120B+", "✓ multi-GPU", "⚠ GGUF/RAM", "⚠ GGUF/RAM"]],
      col_w=[Inches(3.35), Inches(2.7), Inches(2.8), Inches(2.8)], fs=11.5, row_h=Inches(0.36))

# --- vLLM uruchomienie ---
s, y = content("Technika · Vendorzy", "vLLM — uruchomienie serwera",
               "GPU NVIDIA (VRAM ≥ 24 GB), Linux, CUDA 12.x; format HF Safetensors / GGUF")
tb(s, MARGIN, y, Inches(5.5), Inches(0.35), "Instalacja:", size=14, color=INK, bold=True)
code_block(s, MARGIN, y + Inches(0.4), Inches(5.6), [
    "pip install vllm",
    'python3 -c "import vllm; \\',
    '  print(vllm.__version__)"',
])
tb(s, Inches(7.0), y, Inches(5.5), Inches(0.35), "Serwowanie (PLLuM-70B):", size=14, color=INK, bold=True)
code_block(s, Inches(7.0), y + Inches(0.4), Inches(5.5), [
    "vllm serve \\",
    "  CYFRAGOVPL/Llama-PLLuM-70B-chat-2512 \\",
    "  --tensor-parallel-size 2 \\",
    "  --max-model-len 8192 \\",
    "  --port 8080",
])
callout(s, MARGIN, y + Inches(2.6), Inches(11.65), Inches(0.8),
        "Po starcie serwer dostępny pod http://localhost:8080. Ollama: "
        "`ollama run SpeakLeash/bielik-…` lub `ollama run gpt-oss:120b`; "
        "llama.cpp: `cmake -B build -DGGML_CUDA=ON` → `llama-server --model model.gguf`.",
        accent=PURPLE, icon="▸", title="Pozostali vendorzy w skrócie")

# --- LLM ROUTER czym jest + ekosystem ---
s, y = content("Technika · LLM Router", "LLM Router — AI Gateway",
               "Open-source (Apache 2.0) warstwa pośrednicząca: aplikacja ↔ dostawca LLM")
bullets(s, MARGIN, y, Inches(5.9), Inches(2.0), [
    "jeden endpoint dla wielu providerów",
    "load balancing + health checks + streaming",
    "maskowanie / anonimizacja PII",
    "guardrails (treści zabronione)",
], size=14.5, gap=7)
tb(s, Inches(7.0), y - Inches(0.05), Inches(5.5), Inches(0.35), "Ekosystem (repozytoria):",
   size=14, color=INK, bold=True)
table(s, Inches(7.0), y + Inches(0.35), Inches(5.5),
      ["Repo", "Rola"],
      [["llm-router-api", "REST proxy do backendów"],
       ["llm-router-lib", "Python SDK (typowane)"],
       ["llm-router-web", "Flask UI: config + anonymizer"],
       ["llm-router-plugins", "maskery, guardrails, routing, RAG"],
       ["llm-router-services", "guardrails + PII masker (HTTP)"],
       ["llm-router-utils", "CLI: genai-classifier, augmentation"]],
      col_w=[Inches(2.3), Inches(3.2)], fs=11, row_h=Inches(0.42))
code_block(s, MARGIN, y + Inches(2.3), Inches(5.9), [
    "Request → MaskerPipeline →",
    "  GuardrailPipeline →",
    "  UtilsPipeline → Model Provider",
], fs=12)
callout(s, MARGIN, y + Inches(3.55), Inches(5.9), Inches(0.8),
        "fast_masker (regex, 30+ typów PII) · pii_masker (transformer) · "
        "nask_guard / sojka_guard · RAG, semantic routing.",
        accent=CYAN, icon="▸", title="Pluginy")

# --- LABELOWANIE utilsami ---
s, y = content("Technika · Labelowanie", "Automatyczne labelowanie — genai-classifier",
               "CLI z llm-router-utils: JSONL bez etykiet → JSONL z polem labels")
code_block(s, MARGIN, y, Inches(6.4), [
    "genai-classifier \\",
    '  --dataset-dir=resources/.../twitteremo/ \\',
    '  --prompts-dir=.../classifier \\',
    '  --output-dir=.../genailabelled \\',
    '  --llm-router-url=http://localhost:8080 \\',
    '  --model-name=gpt-oss:120b \\',
    '  --temperature=0.0 --num-workers=2 \\',
    '  --n-sample=0 --text-column-name=tekst',
], fs=11.5)
tb(s, Inches(7.05), y - Inches(0.05), Inches(5.4), Inches(0.35), "Jak działa:", size=14, color=INK, bold=True)
bullets(s, Inches(7.05), y + Inches(0.35), Inches(5.4), Inches(2.4), [
    "buduje prompt dla każdego przykładu",
    "wysyła do LLM przez router",
    "parsuje wynik (klasa + confidence + reason)",
    "batch processing, wielowątkowość, retry",
], size=13.5, gap=7)
callout(s, MARGIN, y + Inches(2.75), Inches(11.65), Inches(1.2),
        "temperature=0.0 → determinizm i spójność etykiet · n-sample=0 → wszystkie (5k = 5k wywołań), "
        "n-sample=N do testów · num-workers ↑ = szybciej, ale większe obciążenie. "
        "Następnie konwersja do formatu treningowego (convert_genai_to_training.py).",
        accent=PURPLE, icon="◆", title="Koszt / czas i dobre praktyki")

# --- AUGMENTACJA utilsami ---
s, y = content("Technika · Augmentacja", "Automatyczna augmentacja — genai-data-augmentation",
               "CLI z llm-router-utils: wybór klasy → nowe warianty zachowujące etykietę")
code_block(s, MARGIN, y, Inches(6.4), [
    "genai-data-augmentation \\",
    '  --dataset-path=..._labels.jsonl \\',
    '  --labels=pozytywny \\',
    '  --prompt-file=.../augmentator.prompt \\',
    '  --model-name=gpt-oss:120b \\',
    '  --n-sample=350 --n-examples=5 \\',
    '  --samples-as-examples=2 \\',
    '  --temperature=0.0',
], fs=11.5)
tb(s, Inches(7.05), y - Inches(0.05), Inches(5.4), Inches(0.35),
   "Przykład wyniku (1 input → 5 wariantów):", size=13, color=INK, bold=True)
code_block(s, Inches(7.05), y + Inches(0.4), Inches(5.4), [
    '"tekst": "Super sprawa!",',
    '"labels": ["pozytywny"],',
    '"augmented": [',
    '  "Rzeczywiście świetne!",',
    '  "Podoba mi się!", ... ]',
], fs=11)
callout(s, MARGIN, y + Inches(2.75), Inches(11.65), Inches(1.2),
        "Merge: 5000 ręcznych + ~1750 (350×5) augmentowanych ≈ 6750 przykładów. "
        "n-examples=5 to dobry balans; samples-as-examples=2–3 (in-context); "
        "temperature 0.0 dla spójności, 0.3–0.7 dla różnorodności (ryzyko poprawności).",
        accent=CYAN, icon="◆", title="Merge i strojenie")

# --- UCZENIE: dataset + model + warianty ---
s, y = content("Technika · Uczenie", "Trening klasyfikatora",
               "clarin-pl/twitteremo · 5k train / 500 valid · fine-tuning allegro/herbert-base-cased")
tb(s, MARGIN, y, Inches(5.9), Inches(0.35), "3 warianty (postęp pipeline'u):", size=14, color=INK, bold=True)
for i, (v, d) in enumerate([
    ("Wariant 1", "tylko dane manualne (5k) — baseline"),
    ("Wariant 2", "manual + augmentacja (~1.7k, klasa pozytywny)"),
    ("Wariant 3", "manual + augmentacja + HIL/AL (dump z Web App)")]):
    yy = y + Inches(0.45) + Inches(0.62) * i
    rect(s, MARGIN, yy, Inches(5.9), Inches(0.52), LIGHT, rounded=True)
    rect(s, MARGIN, yy, Pt(4), Inches(0.52), [CYAN, PURPLE, OK][i])
    tb(s, MARGIN + Inches(0.25), yy + Inches(0.04), Inches(1.6), Inches(0.45), v, size=13, color=INK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, MARGIN + Inches(1.75), yy, Inches(4.05), Inches(0.52), d, size=11.5, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
table(s, Inches(7.05), y, Inches(5.4),
      ["Parametr", "Wartość"],
      [["Epoki", "5"], ["Batch size", "32 (eff. 64, grad-accum 2)"],
       ["Learning rate", "3e-6"], ["Max length", "128"],
       ["Scheduler", "cosine"], ["Seed", "42"],
       ["Logowanie", "W&B (acc, F1, conf. matrix)"]],
      col_w=[Inches(2.1), Inches(3.3)], fs=11.5, row_h=Inches(0.4))
callout(s, MARGIN, y + Inches(2.85), Inches(5.9), Inches(1.1),
        "Dump z Web App: brak anotacji → predykcja modelu; 1 ręczna → użyta; "
        ">1 → majority voting; remis → tie-breaker predykcją modelu.",
        accent=OK, icon="✓", title="HIL/AL — wybór etykiety")

# === SEKCJA 4 (podsumowanie) ===
section(4, "Podsumowanie i wnioski", "~6 min · ocena modelu i kierunki dalsze")

# --- PIPELINE + W&B ---
s, y = content("Podsumowanie", "Co zbudowaliśmy — kompletny pipeline")
steps = ["Przygotowanie datasetu (twitteremo 5k/500)",
         "Labelowanie LLM (genai-classifier)",
         "Augmentacja danych (~1.7k, klasa pozytywny)",
         "Merge: 5k manual + ~1.7k augment ≈ 6.7k",
         "Trening 3 wariantów (herbert-base-cased)",
         "Web App: ocena + anotacja (Flask + SQLite)",
         "HITL/AL: poprawki wracają do treningu"]
bullets(s, MARGIN, y, Inches(6.1), Inches(3.8), steps, size=14.5, gap=8)
tb(s, Inches(7.2), y - Inches(0.05), Inches(5.3), Inches(0.35),
   "Ocena po HIL/AL — Weights & Biases:", size=14, color=INK, bold=True)
bullets(s, Inches(7.2), y + Inches(0.4), Inches(5.3), Inches(2.4), [
    "Accuracy i Macro F1 (czułe na imbalance)",
    "Confusion matrix — które klasy mylone",
    "porównanie 3 wariantów na jednym wykresie",
    "dane z Web App: kto i co poprawił",
], size=13.5, gap=7)
callout(s, Inches(7.2), y + Inches(2.9), Inches(5.3), Inches(0.95),
        "Wyniki na żywo: dss2026.radlab.dev + Weights & Biases.",
        accent=CYAN, icon="◎", title="Podgląd w real-time")

# --- WNIOSKI ---
s, y = content("Podsumowanie", "Wnioski")
colw = Inches(3.75)
cols = [
    ("Co zadziałało", OK, [
        "auto-labelowanie ~10×+ szybciej",
        "augmentacja ↑ recall klasy pozytywny",
        "Web App — szybki wgląd w błędy",
        "HIL/AL — najtrudniejsze przykłady"]),
    ("Na co uważać", WARN, [
        "augmentacja bez HIL może szkodzić",
        "temperatura >0 ryzykuje poprawność",
        "tylko jedna klasa augmentowana",
        "LLM może powielać bias danych"]),
    ("Co dalej", PURPLE, [
        "augmentacja wszystkich klas",
        "multi-model routing zadaniowy",
        "pipeline CI/CD dla datasetów",
        "HIL/AL na strumieniu (online)"]),
]
for i, (ttl, col, items) in enumerate(cols):
    x = MARGIN + (colw + Inches(0.2)) * i
    rect(s, x, y, colw, Inches(4.0), LIGHT, rounded=True)
    rect(s, x, y, colw, Inches(0.55), col, rounded=True)
    tb(s, x, y + Inches(0.08), colw, Inches(0.4), ttl, size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    bullets(s, x + Inches(0.25), y + Inches(0.75), colw - Inches(0.45), Inches(3.1), items, size=12.5, gap=9)
callout(s, MARGIN, y + Inches(4.15), Inches(11.65), Inches(0.55),
        "Kontrolowana augmentacja + Active Learning + Human in the Loop = bezpieczniejsza droga do lepszego modelu.",
        accent=CYAN, icon="➜", title=None)

# --- CLOSING ---
closing()

# ============================================================================
out = "DSS_2026_Tutorial_v2.pptx"
prs.save(out)
print(f"OK: {out} — {len(prs.slides.__iter__.__self__._sldIdLst)} slajdów")
