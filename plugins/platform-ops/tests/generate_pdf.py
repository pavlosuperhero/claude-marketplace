#!/usr/bin/env python3
"""
Generates the comprehensive zippo-deployment-spec.pdf using PostScript and ps2pdf.
Reads the specification markdown documents and compiles them into a styled multi-page PDF.
"""

import os
import subprocess
import glob
import re

def escape_ps(text):
    """Escape parenthesis and backslashes for PostScript strings."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def main():
    specs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs_dir = os.path.join(specs_dir, "docs")
    pdf_out = os.path.join(docs_dir, "zippo-deployment-spec.pdf")
    ps_temp = os.path.join(docs_dir, "temp_spec.ps")

    md_files = sorted(glob.glob(os.path.join(docs_dir, "*.md")))

    # PostScript header with basic typography setup
    ps_lines = [
        "%!PS-Adobe-3.0",
        "%%Title: ZIPPO Platform Deployment Specification",
        "%%Creator: Antigravity AI Systems Architect",
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
        "  (ZIPPO PLATFORM SPECIFICATION - ARCHITECTURE & DEPLOYMENT) show",
        "  0.7 0.7 0.7 setrgbcolor",
        "  0.5 setlinewidth",
        "  leftMargin topMargin 10 add moveto rightMargin topMargin 10 add lineto stroke",
        "",
        "  % Footer",
        "  footerFont",
        "  0.4 0.4 0.4 setrgbcolor",
        "  leftMargin bottomMargin moveto",
        "  (CONFIDENTIAL - EPAM ZIPPO PROJECT) show",
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
        "  dup currentY sub bottomMargin 25 add lt {",
        "    pop newPage",
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
        "  (\267 ) show",
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
        "(ZIPPO PLATFORM ARCHITECTURE & SPECIFICATION) show",
        "/currentY 660 def",
        "h2Font",
        "0.3 0.3 0.3 setrgbcolor",
        "leftMargin currentY moveto",
        "(Spec-Driven Development \\(SDD\\) & Test-Driven Development \\(TDD\\) Guide) show",
        "/currentY 630 def",
        "bodyFont",
        "leftMargin currentY moveto",
        "(Generated: September 15, 2026 | Version: 1.0.0 | Status: APPROVED) show",
        "0.8 0.8 0.8 setrgbcolor",
        "leftMargin 615 moveto rightMargin 615 lineto stroke",
        "/currentY 580 def",
    ]

    for md_path in md_files:
        basename = os.path.basename(md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        ps_lines.append(f"% --- Document: {basename} ---")
        in_code_block = False

        for line in lines:
            line_str = line.rstrip()
            if not line_str:
                ps_lines.append("/currentY currentY 6 sub def")
                continue

            if line_str.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                clean = escape_ps(line_str[:85])
                ps_lines.append(f"({clean}) printCode")
                continue

            if line_str.startswith("# "):
                clean = escape_ps(line_str[2:])
                ps_lines.append("/currentY currentY 12 sub def")
                ps_lines.append(f"({clean}) printH1")
            elif line_str.startswith("## "):
                clean = escape_ps(line_str[3:])
                ps_lines.append("/currentY currentY 8 sub def")
                ps_lines.append(f"({clean}) printH2")
            elif line_str.startswith("### "):
                clean = escape_ps(line_str[4:])
                ps_lines.append(f"({clean}) printH2")
            elif line_str.startswith("* ") or line_str.startswith("- "):
                clean = escape_ps(line_str[2:][:90])
                ps_lines.append(f"({clean}) printBullet")
            elif line_str.startswith("|"):
                # Simple table line formatting
                clean = escape_ps(re.sub(r"\s+", " ", line_str)[:90])
                ps_lines.append(f"({clean}) printCode")
            else:
                clean = escape_ps(line_str[:95])
                ps_lines.append(f"({clean}) printBody")

    # Finish last page
    ps_lines.append("newPage")
    ps_lines.append("%%Trailer")
    ps_lines.append("%%Pages: pageNumber 1 sub")
    ps_lines.append("%%EOF")

    with open(ps_temp, "w", encoding="utf-8") as f:
        f.write("\n".join(ps_lines))

    print(f"Written PostScript to {ps_temp}")
    
    # Run ps2pdf
    cmd = ["ps2pdf", ps_temp, pdf_out]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[✓] Generated PDF successfully: {pdf_out}")
        os.remove(ps_temp)
    else:
        print(f"[✗] Error converting PS to PDF: {res.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
