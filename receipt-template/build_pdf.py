#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the editable receipt template to a vector PDF.

Usage
-----
    python3 build_pdf.py                # uses data.json, writes transfer-receipt.pdf
    python3 build_pdf.py out.pdf        # custom output path
    python3 build_pdf.py --example      # writes data.example.json

Requirements: fpdf2, arabic-reshaper, python-bidi
    pip install fpdf2 arabic-reshaper python-bidi

Arabic shaping is done with arabic_reshaper + python-bidi, so the PDF keeps
real selectable text instead of a flattened image.
"""

import json
import sys
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
FONTS = HERE / "fonts"

NAVY = (27, 37, 74)          # #1b254a
_page_width, _page_height = 595, 841   # A4 in points

_reshaper = arabic_reshaper.ArabicReshaper(
    configuration={"delete_harakat": False, "support_ligatures": True}
)

EXAMPLE = {
    "title_ar": "إيصال التحويل",
    "title_en": "Transfer Receipt",
    "date": "2026/10/16",
    "beneficiary_note": "لمستفيد في بنك محلي",
    "reference": "9116102601017005",
    "section_ar": "تفاصيل التحويل",
    "section_en": "Transfer Details",
    "amount": "40 SAR",
    "from_name": "ساره سعود علي الدريويش",
    "from_iban": "SA** **** **** **** **** 5683",
    "from_bank": "Al Rajhi Bank",
    "to_name": "بشرى مشهور",
    "to_iban": "SA3430100949000011328286",
    "purpose": "اخرى",
    "remark": "بحوث وواجبات",
    "website": "Alrajhibank.com.sa",
    "phone": "920 003 344",
}

LABELS = {
    "date_ar": "التاريخ",
    "date_en": "Date",
    "amount_en": "Amount",
    "amount_ar": "المبلغ",
    "from_en": "From",
    "from_ar": "من",
    "to_en": "To",
    "to_ar": "إلى",
    "purpose_en": "Purpose",
    "purpose_ar": "الغرض",
    "remark_en": "Remark",
    "remark_ar": "ملاحظات",
}


def ar(text: str) -> str:
    """Shape + bidi-reorder Arabic so it can be drawn left-to-right."""
    return get_display(_reshaper.reshape(text))


class Receipt(FPDF):
    def __init__(self):
        super().__init__(unit="pt", format=(_page_width, _page_height))
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(False)
        self.c_margin = 0

    def text_at(self, txt, baseline, size, *, right=None, left=None,
                center=None, family="ar", style=""):
        self.set_font(family, style, size)
        self.set_text_color(*NAVY)
        width = self.get_string_width(txt)
        if right is not None:
            x = right - width
        elif center is not None:
            x = center - width / 2
        else:
            x = left
        self.set_xy(x, baseline - 0.8 * size)
        self.cell(width + 0.5, size, txt, align="L")

    # Arabic helpers -------------------------------------------------
    def a(self, txt, baseline, size, **kw):
        self.text_at(ar(txt), baseline, size, **kw)

    def e(self, txt, baseline, size, **kw):
        self.text_at(txt, baseline, size, family="inter", **kw)


def build(data: dict, out: Path) -> Path:
    p = Receipt()
    p.add_font("ar", "", str(FONTS / "PlexArabic-Regular.ttf"))
    p.add_font("ar", "B", str(FONTS / "PlexArabic-SemiBold.ttf"))
    p.add_font("inter", "", str(FONTS / "Inter-400.ttf"))
    p.add_font("inter", "B", str(FONTS / "Inter-600.ttf"))
    p.add_page()

    # ---- header ----
    p.image(str(ASSETS / "alrajhi-logo.png"), x=64.9, y=57.8, w=166.5, h=59.5)
    p.a(data["title_ar"], 85.0, 25.6, right=530.7, style="B")
    p.e(data["title_en"], 124.2, 25.6, right=530.3, style="B")

    # ---- date / reference ----
    p.a(LABELS["date_ar"], 197.7, 14.4, right=530.7, style="B")
    p.e(LABELS["date_en"], 197.7, 14.4, right=491.0)
    p.e(data["date"], 216.9, 14.4, right=528.8)

    p.a(data["beneficiary_note"], 192.1, 14.4, left=64.3)
    p.e(f'Ref. {data["reference"]}', 216.9, 14.4, left=64.3)

    # ---- section ----
    p.e(data["section_en"], 267.3, 14.4, left=76.4)
    p.a(data["section_ar"], 268.1, 14.4, right=518.7)

    # ---- amount ----
    p.e(LABELS["amount_en"], 307.3, 14.4, left=77.1, style="B")
    p.e(data["amount"], 305.7, 14.4, center=298.5)
    p.a(LABELS["amount_ar"], 307.9, 14.4, right=517.9, style="B")

    # ---- from ----
    p.e(LABELS["from_en"], 362.5, 14.4, left=77.1, style="B")
    p.a(LABELS["from_ar"], 363.0, 14.4, right=517.9, style="B")
    p.a(data["from_name"], 341.4, 14.4, center=298.4)
    p.e(data["from_iban"], 363.0, 14.4, center=298.5)
    p.e(data["from_bank"], 384.6, 14.4, center=298.5)

    # ---- to ----
    p.e(LABELS["to_en"], 429.2, 14.4, left=77.1, style="B")
    p.a(LABELS["to_ar"], 429.4, 14.4, right=517.9, style="B")
    p.a(data["to_name"], 417.2, 14.4, center=298.4)
    p.e(data["to_iban"], 438.8, 14.4, center=298.5)

    # ---- purpose / remark ----
    p.e(LABELS["purpose_en"], 474.8, 14.4, left=77.1, style="B")
    p.a(LABELS["purpose_ar"], 475.3, 14.4, right=517.9, style="B")
    p.a(data["purpose"], 475.3, 14.4, center=298.4)

    p.e(LABELS["remark_en"], 508.9, 14.4, left=77.1, style="B")
    p.a(LABELS["remark_ar"], 509.4, 14.4, right=517.9, style="B")
    p.a(data["remark"], 509.4, 14.4, center=298.4)

    # ---- footer ----
    p.image(str(ASSETS / "footer.png"), x=64.3, y=590.5, w=163.2, h=96)
    p.e(data["website"], 623.8, 16.0, right=525.8)
    p.e(data["phone"], 651.0, 24.0, right=530.3)
    p.image(str(ASSETS / "social.png"), x=429.3, y=665.4, w=59.1, h=16.7)

    p.set_title(f'{data["title_ar"]} - {data["title_en"]}')
    p.set_author("Al Rajhi Bank")
    p.set_subject(f'Transfer Receipt {data["reference"]}')
    p.set_creator("receipt-template/build_pdf.py")
    p.set_lang("ar")
    p.output(str(out))
    return out


def main(argv):
    if "--example" in argv:
        target = HERE / "data.example.json"
        target.write_text(json.dumps(EXAMPLE, ensure_ascii=False, indent=2) + "\n")
        print("wrote", target)
        return 0

    data_file = HERE / "data.json"
    data = json.loads(data_file.read_text()) if data_file.exists() else EXAMPLE
    out = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("-") \
        else HERE / "transfer-receipt.pdf"
    build(data, out)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
