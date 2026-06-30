#!/usr/bin/env python3
"""Render a one-page, tailored cover letter PDF in the style of the user's sample.

Layout (mirrors the reference letter the skill was modeled on):
  - Name, centered + bold, at the top
  - A two-column contact row: mailing address on the left, contact links on the right
  - Greeting, body paragraphs (justified), closing line, signature name

The body text (the tailored paragraphs) is written by the model and passed in via
``--body``; this script only owns the deterministic layout and the one-page guarantee.

One-page guarantee
------------------
Cover letters must never spill onto a second page. The script tries a sequence of
progressively more compact typographic presets (font size, leading, paragraph spacing,
margins) and keeps the first one where everything fits on a single US-Letter page. If the
content is too long to fit even at the most compact *readable* preset, the script writes
nothing and exits non-zero with how much overflowed, so the caller shortens the prose
instead of silently producing a two-page letter.

Header config
-------------
Header details come from a JSON config (default ``./coverletter-config.json``):

    {
      "name": "Jordan Goose",
      "address_lines": ["200 University Ave W", "Waterloo, ON, Canada, N2L 3G1"],
      "contact_lines": [
        {"text": "LinkedIn", "url": "https://www.linkedin.com/in/.../"},
        {"text": "jordan.goose@uwaterloo.ca"}
      ]
    }

``address_lines`` fill the left of the contact row; ``contact_lines`` fill the right (each
hyperlinked when a ``url`` is given). Put phone / email / LinkedIn / GitHub there in any
order you like — that is the "customize your header line" knob.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Frame

PAGE_W, PAGE_H = letter  # 612 x 792 pt (US Letter)
BOTTOM_MARGIN = 54       # ~0.75in; signature should never crowd the page edge
LINK_COLOR = "#000000"   # match the understated sample: links read as normal text

# Most-generous to most-compact. Each: (body_pt, leading, space_after, side_margin, top_margin)
PRESETS = [
    (11.0, 15.5, 11.0, 72, 58),
    (11.0, 14.5, 9.0, 72, 54),
    (10.5, 14.0, 8.0, 66, 52),
    (10.5, 13.5, 7.0, 62, 48),
    (10.0, 13.0, 6.0, 58, 44),
    (10.0, 12.5, 5.0, 54, 40),
    (9.5, 12.0, 4.5, 50, 36),
]


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(
            f"ERROR: header config not found at {path}\n"
            "Create coverletter-config.json in this folder first (the skill collects the\n"
            "header details from the user and writes it). Required field: 'name'."
        )
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {path} is not valid JSON: {e}")
    if not cfg.get("name"):
        sys.exit(f"ERROR: {path} is missing the required 'name' field.")
    cfg.setdefault("address_lines", [])
    cfg.setdefault("contact_lines", [])
    return cfg


def read_paragraphs(body_path: str) -> list[str]:
    if body_path == "-":
        raw = sys.stdin.read()
    else:
        with open(body_path, encoding="utf-8") as f:
            raw = f.read()
    parts = re.split(r"\n\s*\n", raw.strip())
    paras = [re.sub(r"[ \t]*\n[ \t]*", " ", p.strip()) for p in parts if p.strip()]
    if not paras:
        where = "stdin" if body_path == "-" else body_path
        sys.exit(f"ERROR: body ({where}) contains no paragraphs.")
    return paras


def slugify_company(name: str) -> str:
    name = re.sub(
        r"\b(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|plc|gmbh)\b\.?",
        "",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")
    return name or "Company"


def _link(text: str, url: str | None) -> str:
    safe = escape(text)
    if url:
        safe_url = escape(url, {'"': "&quot;"})
        return f'<a href="{safe_url}" color="{LINK_COLOR}">{safe}</a>'
    return safe


def build_flowables(cfg, paras, greeting, closing, date, fs, leading, space_after, col_width):
    name = cfg["name"]
    name_style = ParagraphStyle(
        "name", fontName="Times-Bold", fontSize=fs + 5,
        leading=(fs + 5) * 1.15, alignment=TA_CENTER, spaceAfter=fs * 0.6,
    )
    addr_style = ParagraphStyle(
        "addr", fontName="Times-Roman", fontSize=fs, leading=fs * 1.25, alignment=TA_LEFT,
    )
    contact_style = ParagraphStyle(
        "contact", fontName="Times-Roman", fontSize=fs, leading=fs * 1.25, alignment=TA_RIGHT,
    )
    body_style = ParagraphStyle(
        "body", fontName="Times-Roman", fontSize=fs, leading=leading,
        alignment=TA_JUSTIFY, spaceAfter=space_after,
    )
    plain_style = ParagraphStyle(
        "plain", fontName="Times-Roman", fontSize=fs, leading=leading, alignment=TA_LEFT,
    )

    flow = [Paragraph(escape(name), name_style)]

    # Contact row: address on the left, contact links on the right.
    addr_html = "<br/>".join(escape(line) for line in cfg["address_lines"] if line)
    contact_html = "<br/>".join(
        _link(c.get("text", ""), c.get("url")) for c in cfg["contact_lines"] if c.get("text")
    )
    if addr_html or contact_html:
        # Two equal columns split the usable frame width.
        tbl = Table(
            [[Paragraph(addr_html or "&nbsp;", addr_style),
              Paragraph(contact_html or "&nbsp;", contact_style)]],
            colWidths=[col_width, col_width],
        )
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flow.append(tbl)

    flow.append(Spacer(1, fs * 1.6))
    if date:
        flow.append(Paragraph(escape(date), plain_style))
        flow.append(Spacer(1, fs * 1.2))
    flow.append(Paragraph(escape(greeting), plain_style))
    flow.append(Spacer(1, space_after))
    for p in paras:
        flow.append(Paragraph(escape(p), body_style))
    flow.append(Spacer(1, fs * 0.4))
    flow.append(Paragraph(escape(closing), plain_style))
    flow.append(Spacer(1, fs * 0.3))
    flow.append(Paragraph(escape(name), plain_style))
    return flow


def try_render(cfg, paras, greeting, closing, date, preset):
    fs, leading, space_after, side, top = preset
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    half = (PAGE_W - 2 * side) / 2.0
    flow = build_flowables(cfg, paras, greeting, closing, date, fs, leading, space_after, half)

    frame = Frame(
        side, BOTTOM_MARGIN, PAGE_W - 2 * side, PAGE_H - top - BOTTOM_MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    remaining = list(flow)
    frame.addFromList(remaining, c)
    if remaining:
        return None  # did not all fit on one page
    c.showPage()
    c.save()
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description="Generate a one-page cover letter PDF.")
    ap.add_argument("--config", default="coverletter-config.json", help="header config JSON")
    ap.add_argument("--body", required=True, help="text file of body paragraphs (blank-line separated), or '-' to read them from stdin")
    ap.add_argument("--company", required=True, help="company name (used for the default filename)")
    ap.add_argument("--out", help="output path (default: coverletter/<Company>-coverletter.pdf, created if missing)")
    ap.add_argument("--greeting", default="Dear Hiring Manager,")
    ap.add_argument("--closing", default="Sincerely,")
    ap.add_argument("--date", default="", help="optional date line above the greeting")
    args = ap.parse_args()

    cfg = load_config(args.config)
    paras = read_paragraphs(args.body)
    out = args.out or os.path.join("coverletter", f"{slugify_company(args.company)}-coverletter.pdf")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    words = sum(len(p.split()) for p in paras)

    for preset in PRESETS:
        data = try_render(cfg, paras, args.greeting, args.closing, args.date, preset)
        if data is not None:
            with open(out, "wb") as f:
                f.write(data)
            print(f"OK: wrote {out}  (1 page, body font {preset[0]}pt, "
                  f"{len(paras)} paragraphs, ~{words} words)")
            return 0

    sys.exit(
        f"ERROR: {len(paras)} paragraphs (~{words} words) do not fit on one page even at the "
        f"most compact readable preset ({PRESETS[-1][0]}pt).\n"
        "Shorten the body — aim for 3-4 tight paragraphs, ~250-330 words total — and rerun."
    )


if __name__ == "__main__":
    raise SystemExit(main())
