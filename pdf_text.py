"""Shared ReportLab paragraphs: logical wrapping, shaped Arabic, styled bidi runs.

Report language controls layout, never a string's glyph coverage. XML input is
application markup; callers must escape user/model text before constructing it.
"""
from copy import deepcopy
from html import escape
from pathlib import Path
import re
import threading

import arabic_reshaper
from bidi import algorithm as bidi
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph as BaseParagraph

ARABIC = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]")
_FONT_LOCK = threading.Lock()
_CONTROLS = dict.fromkeys(map(ord, "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"))


def register_arabic_font():
    with _FONT_LOCK:
        if "Amiri" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("Amiri", str(Path(__file__).parent / "fonts/Amiri-Regular.ttf")))
            pdfmetrics.registerFontFamily("Amiri", normal="Amiri", bold="Amiri", italic="Amiri", boldItalic="Amiri")


def _visual_runs(parts):
    """Bidi reorders characters AND their style ownership, not whole strings.

    Shape within each style span (our markup never cuts an Arabic word), then
    resolve the entire logical line so Latin names, figures and punctuation
    retain their correct relative order across span boundaries.
    """
    text, owners = "", []
    for fragment, value in parts:
        shaped = arabic_reshaper.reshape(value.translate(_CONTROLS))
        text += shaped
        owners.extend([fragment] * len(shaped))
    if not text:
        return []
    storage = bidi.get_empty_storage()
    level = bidi.get_base_level(text)
    storage.update(base_level=level, base_dir=("L", "R")[level])
    bidi.get_embedding_levels(text, storage, False, False)
    for char, owner in zip(storage["chars"], owners):
        char["owner"] = owner
    for operation in (bidi.explicit_embed_and_overrides, bidi.resolve_weak_types,
                      bidi.resolve_neutral_types, bidi.resolve_implicit_levels,
                      bidi.reorder_resolved_levels, bidi.apply_mirroring):
        operation(storage, False)
    runs = []
    for char in storage["chars"]:
        owner, value = char["owner"], char["ch"]
        font = "Amiri" if ARABIC.search(value) else owner.fontName
        key = (font, owner.fontSize, owner.textColor.hexval())
        if runs and runs[-1][0] == key:
            runs[-1] = (key, runs[-1][1] + value)
        else:
            runs.append((key, value))
    return runs


def _line_width(parts):
    # Bidi changes visual order, not advances. Measuring shaped logical runs
    # avoids running the full bidi algorithm for every candidate word boundary.
    width = 0
    for owner, value in parts:
        text = arabic_reshaper.reshape(value.translate(_CONTROLS))
        runs = []
        for char in text:
            font = "Amiri" if ARABIC.search(char) else owner.fontName
            if runs and runs[-1][0] == font:
                runs[-1] = (font, runs[-1][1] + char)
            else:
                runs.append((font, char))
        width += sum(pdfmetrics.stringWidth(text, font, owner.fontSize) for font, text in runs)
    return width


class Paragraph(BaseParagraph):
    """Pure Latin uses ReportLab; any Arabic uses the same mixed-script path."""
    def __init__(self, text, style, bulletText=None, frags=None, **kwargs):
        super().__init__(text, style, bulletText=bulletText, frags=frags, **kwargs)
        self._logical = deepcopy(self.frags) if frags is None else None
        self._mixed = self._logical is not None and any(ARABIC.search(getattr(f, "text", "")) for f in self._logical)
        self._prepared_width = None

    def wrap(self, availWidth, availHeight):
        if not self._mixed:
            return super().wrap(availWidth, availHeight)
        if self._prepared_width == availWidth:
            return super().wrap(availWidth, availHeight)
        register_arabic_font()
        usable = max(1, availWidth - self.style.leftIndent - self.style.rightIndent - abs(self.style.firstLineIndent) - 2)
        lines, current = [], []

        def flush():
            nonlocal current
            lines.append("".join(
                f'<font name="{font}" size="{size}" color="{color.replace("0x", "#")}">{escape(value)}</font>'
                for (font, size, color), value in _visual_runs(current)
            ))
            current = []

        for fragment in self._logical:
            if getattr(fragment, "lineBreak", False):
                flush()
                continue
            # Keep whitespace ownership and style boundaries, without inserting
            # spaces between fragments that were adjacent in the original XML.
            for word in re.findall(r"\s+|\S+", getattr(fragment, "text", "")):
                if not current and word.isspace():
                    continue
                if current and _line_width(current + [(fragment, word)]) > usable:
                    flush()
                    if word.isspace():
                        continue
                if _line_width([(fragment, word)]) > usable:
                    # Bounded input can still include one very long word/URL.
                    chunk = ""
                    for char in word:
                        if chunk and _line_width([(fragment, chunk + char)]) > usable:
                            current.append((fragment, chunk)); flush(); chunk = ""
                        chunk += char
                    if chunk:
                        current.append((fragment, chunk))
                else:
                    current.append((fragment, word))
        if current:
            flush()
        BaseParagraph.__init__(self, "<br/>".join(lines), self.style, bulletText=self.bulletText)
        self._prepared_width = availWidth
        return super().wrap(availWidth, availHeight)
