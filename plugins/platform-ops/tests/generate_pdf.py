#!/usr/bin/env python3
"""
Generates the platform deployment specification using PostScript and ps2pdf.
Reads the specification markdown documents and compiles them into a styled multi-page PDF.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from textwrap import wrap


# Built-in PostScript fonts need ASCII approximations for these Markdown glyphs.
PS_CHARACTERS = str.maketrans({
    "─": "-", "━": "-", "│": "|", "═": "=", "▼": "v",
    "┌": "+", "┐": "+", "└": "+", "┘": "+", "┬": "+", "┴": "+",
    "├": "+", "┤": "+", "┼": "+", "→": "->", "←": "<-",
    "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
})


def printable(text):
    return text.translate(PS_CHARACTERS).encode("ascii", "ignore").decode("ascii")


def escape_ps(text):
    """Escape parenthesis and backslashes for PostScript strings."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compile documentation markdown files into a styled PDF."
    )
    parser.add_argument(
        "-d", "--docs-dir",
        dest="docs_dir",
        default=None,
        help="Path to directory containing markdown specification files."
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_pdf",
        default=None,
        help="Target path for generated PDF."
    )
    parser.add_argument(
        "--title", default="Platform Deployment Specification",
        help="Document title used on the cover and in the PDF metadata.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    docs_dir = Path(args.docs_dir) if args.docs_dir else Path(__file__).resolve().parents[1] / "docs"
    pdf_out = Path(args.output_pdf) if args.output_pdf else docs_dir / "platform-deployment-spec.pdf"
    md_files = sorted(docs_dir.glob("*.md"))
    if not md_files:
        print(f"Error: No Markdown files in {docs_dir}", file=sys.stderr)
        return 1

    title = printable(" ".join(args.title.split()))

    # PostScript header with basic typography setup
    ps_lines = [
        "%!PS-Adobe-3.0",
        f"%%Title: {title}",
        "%%Creator: Platform Ops",
        "%%Pages: (atend)",
        "%%BoundingBox: 0 0 595 842", # A4
        "%%EndComments",
        "",
        "/pageWidth 595 def",
        "/pageHeight 842 def",
        "/leftMargin 50 def",
        "/rightMargin 545 def",
        "/bottomMargin 50 def",
        "/topMargin 780 def",
        "",
        "/headerFont { /Helvetica-Bold findfont 8 scalefont setfont } def",
        "/footerFont { /Helvetica findfont 8 scalefont setfont } def",
        "/titleFont { /Helvetica-Bold findfont 18 scalefont setfont } def",
        "/h1Font { /Helvetica-Bold findfont 13 scalefont setfont } def",
        "/h2Font { /Helvetica-Bold findfont 11 scalefont setfont } def",
        "/bodyFont { /Helvetica findfont 9.5 scalefont setfont } def",
        "/codeFont { /Courier findfont 8 scalefont setfont } def",
        "",
        "/pageNumber 1 def",
        "/currentY topMargin def",
        "",
        "/newPage {",
        "  % Header",
        "  headerFont",
        "  0.4 0.4 0.4 setrgbcolor",
        "  leftMargin topMargin 15 add moveto",
        "  (PLATFORM OPS - ARCHITECTURE & DEPLOYMENT) show",
        "  0.7 0.7 0.7 setrgbcolor",
        "  0.5 setlinewidth",
        "  leftMargin topMargin 10 add moveto rightMargin topMargin 10 add lineto stroke",
        "",
        "  % Footer",
        "  footerFont",
        "  0.4 0.4 0.4 setrgbcolor",
        "  leftMargin bottomMargin moveto",
        "  (Platform Operations) show",
        "  rightMargin 40 sub bottomMargin moveto",
        "  (Page ) show pageNumber 10 string cvs show",
        "  0.7 0.7 0.7 setrgbcolor",
        "  0.5 setlinewidth",
        "  leftMargin bottomMargin 10 add moveto rightMargin bottomMargin 10 add lineto stroke",
        "",
        "  showpage",
        "  /pageNumber pageNumber 1 add def",
        "  /currentY topMargin def",
        "} def",
        "",
        "/checkPage {",
        "  currentY exch sub bottomMargin 25 add lt {",
        "    newPage",
        "  } if",
        "} def",
        "",
        "/printH1 {",
        "  25 checkPage",
        "  0.1 0.2 0.5 setrgbcolor",
        "  h1Font",
        "  leftMargin currentY moveto",
        "  show",
        "  /currentY currentY 18 sub def",
        "} def",
        "",
        "/printH2 {",
        "  20 checkPage",
        "  0.2 0.2 0.2 setrgbcolor",
        "  h2Font",
        "  leftMargin currentY moveto",
        "  show",
        "  /currentY currentY 15 sub def",
        "} def",
        "",
        "/printBody {",
        "  14 checkPage",
        "  0 0 0 setrgbcolor",
        "  bodyFont",
        "  leftMargin currentY moveto",
        "  show",
        "  /currentY currentY 12 sub def",
        "} def",
        "",
        "/printBullet {",
        "  14 checkPage",
        "  0 0 0 setrgbcolor",
        "  bodyFont",
        "  leftMargin 10 add currentY moveto",
        r"  (\267 ) show",
        "  show",
        "  /currentY currentY 12 sub def",
        "} def",
        "",
        "/printCode {",
        "  12 checkPage",
        "  0.15 0.15 0.15 setrgbcolor",
        "  codeFont",
        "  leftMargin 15 add currentY moveto",
        "  show",
        "  /currentY currentY 10 sub def",
        "} def",
        "",
        "% Title Page Block",
        "titleFont",
        "0.1 0.2 0.5 setrgbcolor",
        "leftMargin 700 moveto",
        f"({escape_ps(title)}) show",
        "/currentY 660 def",
        "h2Font",
        "0.3 0.3 0.3 setrgbcolor",
        "leftMargin currentY moveto",
        "(Spec-Driven Development \\(SDD\\) & Test-Driven Development \\(TDD\\) Guide) show",
        "/currentY 630 def",
        "bodyFont",
        "leftMargin currentY moveto",
        "0.8 0.8 0.8 setrgbcolor",
        "leftMargin 615 moveto rightMargin 615 lineto stroke",
        "/currentY 580 def",
    ]

    for md_path in md_files:
        try:
            lines = md_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            print(f"Error reading {md_path}: {error}", file=sys.stderr)
            return 1

        in_code_block = False
        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue
            if not line.strip():
                ps_lines.append("/currentY currentY 6 sub def")
                continue

            if in_code_block or line.startswith("|"):
                procedure, content, width = "printCode", line, 85
            elif line.startswith("# "):
                procedure, content, width = "printH1", line[2:], 60
            elif line.startswith(("## ", "### ")):
                procedure, content, width = "printH2", line.lstrip("# "), 75
            elif line.startswith(("* ", "- ")):
                procedure, content, width = "printBullet", line[2:], 90
            else:
                procedure, content, width = "printBody", line, 95

            for segment in wrap(printable(content), width=width, drop_whitespace=False):
                ps_lines.append(f"({escape_ps(segment)}) {procedure}")

    # Finish last page
    ps_lines.append("newPage")
    ps_lines.append("%%Trailer")
    ps_lines.append("%%Pages: pageNumber 1 sub")
    ps_lines.append("%%EOF")

    try:
        with TemporaryDirectory(prefix=".platform-spec-", dir=pdf_out.parent) as temp_dir:
            ps_path = Path(temp_dir) / "spec.ps"
            pdf_path = Path(temp_dir) / "spec.pdf"
            ps_path.write_text("\n".join(ps_lines), encoding="ascii")
            subprocess.run(
                ["ps2pdf", ps_path, pdf_path], capture_output=True, text=True,
                check=True, timeout=120,
            )
            os.replace(pdf_path, pdf_out)
    except subprocess.CalledProcessError as error:
        print(f"Error converting PostScript to PDF: {error.stderr}", file=sys.stderr)
        return 1
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Error generating PDF: {error}", file=sys.stderr)
        return 1

    print(f"[✓] Generated PDF successfully: {pdf_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
