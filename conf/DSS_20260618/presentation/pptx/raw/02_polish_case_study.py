#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ujednolica 4 wstawione slajdy studium przypadku (Helpi) z resztą decku
DSS_2026_Tutorial.pptx:

  * dodaje stopkę ("DSS 2026 AI Edition · Studium przypadku · Helpi" + numer),
  * zamienia złoty pasek nad tytułem na cyan podkreślenie POD tytułem
    (spójne z pozostałymi slajdami treściowymi),
  * renumeruje stopki w całym decku (po wstawieniu slajdów numery się przesunęły).

Skrypt jest idempotentny: stopki dodaje tylko tam, gdzie ich brak, a cyan
podkreślenie tylko gdy obecny jest oryginalny złoty pasek (usuwany przy okazji).
"""

import os
import re
import sys

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "DSS_2026_Tutorial.pptx")

# --- brand (zgodne z generatorem) ---
CYAN = RGBColor(0x00, 0xBE, 0xFE)
GRAY = RGBColor(0x6B, 0x64, 0x78)
LIGHT = RGBColor(0xF2, 0xF1, 0xF6)
GOLD = "B58827"                      # kolor oryginalnego paska nad tytułem
MARGIN = Inches(0.84)
SLIDE_W = Inches(13.333)
SECTION = "Studium przypadku · Helpi"

AFTER_TITLE = "Pętla HITL"
BEFORE_TITLE = "Interaktywna sesja anotacyjna"
FOOTER_TAG = "DSS 2026 AI Edition"


def _title(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip().split("\n")[0]
    return ""


def _no_shadow(shape):
    shape.shadow.inherit = False
    return shape


def has_footer(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and FOOTER_TAG in sh.text_frame.text:
            return True
    return False


def add_footer(slide, page):
    line = _no_shadow(slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(7.04), SLIDE_W, Pt(1.2)))
    line.fill.solid(); line.fill.fore_color.rgb = LIGHT
    line.line.fill.background()

    left = slide.shapes.add_textbox(MARGIN, Inches(7.08), Inches(9), Inches(0.32))
    p = left.text_frame.paragraphs[0]
    r = p.add_run(); r.text = f"{FOOTER_TAG}  ·  {SECTION}"
    r.font.size = Pt(9); r.font.color.rgb = GRAY; r.font.name = "Arial"

    right = slide.shapes.add_textbox(Inches(11.6), Inches(7.08), Inches(0.9), Inches(0.32))
    p2 = right.text_frame.paragraphs[0]; p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run(); r2.text = str(page)
    r2.font.size = Pt(9); r2.font.color.rgb = GRAY; r2.font.name = "Arial"


def title_shape(slide):
    """Kształt tytułu = największa czcionka w górnej części slajdu."""
    best, best_fs = None, 0
    for sh in slide.shapes:
        if not (sh.has_text_frame and sh.text_frame.text.strip()):
            continue
        if sh.top is None or sh.top >= Inches(2.0):
            continue
        for par in sh.text_frame.paragraphs:
            for run in par.runs:
                if run.font.size and run.font.size.pt > best_fs:
                    best_fs, best = run.font.size.pt, sh
    return best


def gold_bar_above(slide, title):
    for sh in slide.shapes:
        if sh.width is None or sh.height is None or sh.top is None:
            continue
        if sh.height >= Inches(0.3) or sh.width <= Inches(2):
            continue
        if GOLD not in sh._element.xml:
            continue
        if sh.top < title.top and abs(int(sh.left) - int(title.left)) < int(Inches(0.4)):
            return sh
    return None


CYAN_HEX = "00BEFE"


def remove_existing_underlines(slide):
    """Usuwa wcześniej dodane cyan podkreślenia (idempotencja)."""
    for sh in list(slide.shapes):
        if sh.width is None or sh.height is None:
            continue
        if (sh.height <= Inches(0.1) and Inches(1.3) <= sh.width <= Inches(1.7)
                and CYAN_HEX in sh._element.xml):
            sh._element.getparent().remove(sh._element)


def add_underline(slide, title):
    # pod całym boxem tytułu (działa dla tytułów 1- i wieloliniowych)
    top = title.top + title.height + Inches(0.05)
    bar = _no_shadow(slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, title.left, top, Inches(1.5), Pt(3.5)))
    bar.fill.solid(); bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()


def renumber_footers(prs):
    """Numer w prawym-dolnym polu stopki = pozycja slajdu (1-based)."""
    for i, slide in enumerate(prs.slides, start=1):
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            if sh.left is None or sh.top is None:
                continue
            txt = sh.text_frame.text.strip()
            if (re.fullmatch(r"\d+", txt) and sh.left > Inches(11)
                    and sh.top > Inches(6.9)):
                for par in sh.text_frame.paragraphs:
                    for run in par.runs:
                        if re.fullmatch(r"\d+", run.text.strip()):
                            run.text = str(i)


def main():
    if not os.path.exists(DECK):
        sys.exit(f"Brak pliku: {DECK}")
    prs = Presentation(DECK)
    titles = [_title(s) for s in prs.slides]

    start = next((i for i, t in enumerate(titles)
                  if AFTER_TITLE.lower() in t.lower()), None)
    end = next((i for i, t in enumerate(titles)
                if BEFORE_TITLE.lower() in t.lower()), None)
    if start is None or end is None or end <= start + 1:
        sys.exit("Nie znaleziono zakresu slajdów studium przypadku.")
    case_idx = list(range(start + 1, end))
    print(f"Slajdy studium przypadku: indeksy {case_idx}")

    for idx in case_idx:
        slide = prs.slides[idx]
        if not has_footer(slide):
            add_footer(slide, idx + 1)
            print(f"  idx {idx}: dodano stopkę (nr {idx + 1})")
        title = title_shape(slide)
        if title is not None:
            bar = gold_bar_above(slide, title)
            if bar is not None:
                bar._element.getparent().remove(bar._element)
            remove_existing_underlines(slide)
            add_underline(slide, title)
            print(f"  idx {idx}: cyan podkreślenie pod tytułem"
                  + (" (usunięto złoty pasek)" if bar is not None else ""))
        else:
            print(f"  idx {idx}: brak tytułu tekstowego — tylko stopka")

    renumber_footers(prs)
    prs.save(DECK)
    print(f"OK: {DECK} — {len(titles)} slajdów, stopki zrenumerowane.")


if __name__ == "__main__":
    main()
