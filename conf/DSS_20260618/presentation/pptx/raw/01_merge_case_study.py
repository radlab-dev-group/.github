#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wstawia 4 slajdy studium przypadku (projekt Helpi) z pliku CWR do
DSS_2026_Tutorial.pptx — w miejsce po opisie pełnej pętli HITL/AL, a przed
slajdem z interaktywną sesją anotacyjną.

Slajdy kopiowane są 1:1 (kształty + obrazy, z remapowaniem relacji),
zachowując oryginalny wygląd. Kolory są w większości jawne (srgbClr),
a odwołania motywu (dk1=czerń, lt1=biel) i czcionki (Arial/Calibri)
rozwiązują się tak samo w docelowym motywie.
"""

import copy
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "DSS_2026_Tutorial.pptx")
SRC = os.path.join(HERE, "CWR - DSSAI26-Prezentacja_Szablon_PL.pptx")

AFTER_TITLE = "Pętla HITL"                    # slajd, PO którym wstawiamy
BEFORE_TITLE = "Interaktywna sesja anotacyjna"  # slajd, PRZED którym wstawiamy

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
REL_ATTRS = (qn("r:embed"), qn("r:link"), qn("r:id"), qn("r:pict"),
             qn("r:dm"), qn("r:lo"), qn("r:qs"), qn("r:cs"))


def _slide_title(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip().split("\n")[0]
    return ""


def _remap_rels(src_part, dst_part, element):
    """Przepisuje wszystkie relacje (obrazy, hiperłącza) z części źródłowej
    do docelowej i podmienia identyfikatory rId w skopiowanym XML."""
    seen = {}
    for el in element.iter():
        for attr in REL_ATTRS:
            old = el.get(attr)
            if not old or old not in src_part.rels:
                continue
            if old not in seen:
                rel = src_part.rels[old]
                if rel.is_external:
                    seen[old] = dst_part.rels.get_or_add_ext_rel(
                        rel.reltype, rel.target_ref)
                else:
                    seen[old] = dst_part.relate_to(rel.target_part, rel.reltype)
            el.set(attr, seen[old])


def _copy_slide(src_slide, dst_prs, blank_layout):
    dst_slide = dst_prs.slides.add_slide(blank_layout)
    # białe tło (slajdy źródłowe są na bieli — lt1)
    dst_slide.background.fill.solid()
    dst_slide.background.fill.fore_color.rgb = WHITE
    # wyczyść ewentualne placeholdery z blank layoutu
    dst_tree = dst_slide.shapes._spTree
    for shp in list(dst_slide.shapes):
        dst_tree.remove(shp._element)
    # skopiuj zawartość spTree (poza nvGrpSpPr/grpSpPr) ze slajdu źródłowego
    src_tree = src_slide.shapes._spTree
    for child in list(src_tree):
        local = child.tag.split("}")[-1]
        if local in ("nvGrpSpPr", "grpSpPr"):
            continue
        dst_tree.append(copy.deepcopy(child))
    # remap relacji (obrazy itd.)
    _remap_rels(src_slide.part, dst_slide.part, dst_tree)
    return dst_slide


def main():
    if not os.path.exists(DEST):
        sys.exit(f"Brak pliku docelowego: {DEST}")
    if not os.path.exists(SRC):
        sys.exit(f"Brak pliku źródłowego: {SRC}")

    dst = Presentation(DEST)
    src = Presentation(SRC)
    blank = dst.slide_layouts[6]

    titles = [_slide_title(s) for s in dst.slides]
    # indeks slajdu kotwiczącego (przed którym wstawiamy)
    anchor_idx = next((i for i, t in enumerate(titles)
                       if BEFORE_TITLE.lower() in t.lower()), None)
    if anchor_idx is None:
        sys.exit(f"Nie znaleziono slajdu '{BEFORE_TITLE}' w {DEST}")
    # walidacja: poprzedni slajd to opis pętli
    prev_t = titles[anchor_idx - 1] if anchor_idx > 0 else ""
    if AFTER_TITLE.lower() not in prev_t.lower():
        print(f"UWAGA: slajd przed kotwicą to '{prev_t}', oczekiwano '{AFTER_TITLE}'.")

    n_before = len(titles)
    new_slides = [_copy_slide(s, dst, blank) for s in src.slides]
    print(f"Skopiowano {len(new_slides)} slajdów z CWR.")

    # przesuń nowo dodane (są na końcu sldIdLst) przed slajd kotwiczący
    sldIdLst = dst.slides._sldIdLst
    ids = list(sldIdLst)
    moved = ids[n_before:]          # ostatnie N = nowe slajdy
    anchor_el = ids[anchor_idx]     # element kotwicy (pozycja sprzed dodania)
    for sid in moved:
        sldIdLst.remove(sid)
    for sid in moved:               # zachowanie kolejności
        anchor_el.addprevious(sid)

    dst.save(DEST)
    final = [_slide_title(s) for s in Presentation(DEST).slides]
    print(f"OK: {DEST} — {len(final)} slajdów.")
    lo = anchor_idx - 1
    for i in range(lo, lo + len(moved) + 2):
        if 0 <= i < len(final):
            mark = "  << wstawione" if lo < i <= lo + len(moved) else ""
            print(f"  {i:2d}  {final[i][:50]!r}{mark}")


if __name__ == "__main__":
    main()
