#!/usr/bin/env python3
"""Sherpa resume helper: PDF/Word/Markdown in, checked quotes, clean PDF out.

    resume_io.py extract <file>                    text + layout/ATS flags (JSON)
    resume_io.py verify-quotes <resume> <quotes.json>
    resume_io.py render <resume.md|.html> <out.pdf> [--paper letter|a4]

Prints JSON. Uses pdftotext / pypdf / weasyprint / pandoc / Chrome when present,
and says what to install when they are not.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path


def out(obj, code=0):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    sys.exit(code)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- extract

def pdf_text(path):
    """Return (reading_order_text, layout_text, pages, method)."""
    if shutil.which("pdftotext"):
        raw = run(["pdftotext", "-enc", "UTF-8", str(path), "-"])
        lay = run(["pdftotext", "-enc", "UTF-8", "-layout", str(path), "-"])
        if raw.returncode == 0:
            pages = max(1, raw.stdout.count("\f"))
            return raw.stdout, lay.stdout, pages, "pdftotext"
    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit(out({"ok": False, "error": "No PDF text tool found.",
                              "install": ["poppler (pdftotext): https://poppler.freedesktop.org",
                                          "or: pip install pypdf"],
                              "fallback": "Paste the resume text instead."}, 2))
    reader = PdfReader(str(path))
    raw = "\f".join((p.extract_text() or "") for p in reader.pages)
    try:
        lay = "\f".join((p.extract_text(extraction_mode="layout") or "") for p in reader.pages)
    except TypeError:  # old pypdf without layout mode
        lay = raw
    return raw, lay, len(reader.pages), "pypdf"


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    lines = ["".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S)) for p in paras]
    return html.unescape("\n".join(lines))


def image_count(path):
    if not shutil.which("pdfimages"):
        return None
    r = run(["pdfimages", "-list", str(path)])
    if r.returncode != 0:
        return None
    return max(0, len(r.stdout.strip().splitlines()) - 2)  # two header lines


STOP = set("""a an and are as at be by for from has have in into is it its of on or our that the
their this to was we were with will you your i my me he she they them his her not but also
over per all can new using used use within across more most""".split())


def column_lines(layout_text):
    """Lines with substantial text on both sides of a wide gap: the mark of a multi-column page.
    Right-aligned dates ("Acme Corp        2019-2022") don't count because the right side is short."""
    n = 0
    for line in layout_text.splitlines():
        parts = [p for p in re.split(r"\s{5,}", line.strip()) if p]
        if len(parts) >= 2 and len(parts[0]) >= 15 and len(parts[1]) >= 15:
            n += 1
    return n


def flags_for(text, layout_text, pages, path, kind):
    flags = []
    def flag(code, detail):
        flags.append({"code": code, "detail": detail})

    chars = len(re.sub(r"\s", "", text))
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-']*", text)
    if kind == "pdf" and chars < 50 * pages:
        flag("no_text_layer", "Little or no extractable text. This looks like a scanned or image-only PDF, "
             "which most screening software reads as blank. Run OCR (e.g. `ocrmypdf in.pdf out.pdf`) or paste the text.")
    if kind == "pdf" and layout_text:
        nonempty = [l for l in layout_text.splitlines() if l.strip()]
        cols = column_lines(layout_text)
        if cols >= 4 and cols >= 0.15 * max(1, len(nonempty)):
            flag("suspected_columns", f"{cols} of {len(nonempty)} lines have text side by side. Multi-column layouts "
                 "often scramble reading order in screening software. A single column is safer.")
    if chars >= 50 * pages:
        if len(words) < 200:
            flag("too_short", f"{len(words)} words. Most resumes need 350-900 words to show enough evidence.")
        if pages > 2 or len(words) > 1100:
            flag("too_long", f"{pages} page(s), {len(words)} words. Aim for one to two pages.")
        if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
            flag("missing_email", "No email address found.")
        phones = re.findall(r"\+?\(?\d[\d \t().-]{6,}\d", text)
        if not any(9 <= len(re.sub(r"\D", "", p)) <= 15 and not re.fullmatch(r"\(?\d{4}\s*-\s*\d{4}\)?", p.strip())
                   for p in phones):
            flag("missing_phone", "No phone number found.")
        if not re.search(r"(linkedin\.com|github\.com|https?://|www\.)", text, re.I):
            flag("missing_links", "No LinkedIn, portfolio or other link found.")
        odd = [c for c in text if unicodedata.category(c) in ("Co", "Cs") or c == "\ufffd"
               or "\ufb00" <= c <= "\ufb06" or (unicodedata.category(c) == "Cc" and c not in "\n\r\t\f")]
        if len(odd) >= 3:
            flag("odd_characters", f"{len(odd)} unusual characters (e.g. {sorted(set(odd))[:5]!r}). "
                 "Icon fonts, ligatures or broken encoding can garble what a parser sees.")
        lower = [w.lower().strip(".-'") for w in words]
        counts = Counter(w for w in lower if len(w) > 2 and w not in STOP)
        if counts:
            top, n = counts.most_common(1)[0]
            if n >= 12 and n >= 0.03 * len(lower):
                flag("keyword_stuffing", f"'{top}' appears {n} times ({n * 100 // len(lower)}% of words). "
                     "Heavy repetition reads as stuffing to both software and people.")
        short_lines = [l.strip().lower() for l in text.splitlines() if 0 < len(l.strip()) < 40]
        missing = [h for h in ("experience", "education", "skills")
                   if not any(h in l for l in short_lines)]
        if missing:
            flag("nonstandard_headings", f"No clear heading for: {', '.join(missing)}. "
                 "Screening software looks for standard section names.")
    if kind == "pdf":
        imgs = image_count(path)
        if imgs:
            flag("images_present", f"{imgs} image(s) in the PDF. Any text inside images (logos, skill bars, "
                 "headers) is invisible to screening software.")
    return flags, len(words)


def extract(path):
    path = Path(path)
    if not path.exists():
        out({"ok": False, "error": f"File not found: {path}"}, 2)
    ext = path.suffix.lower()
    layout, pages = "", 1
    if ext == ".pdf":
        text, layout, pages, method = pdf_text(path)
        kind = "pdf"
    elif ext == ".docx":
        text, method, kind = docx_text(path), "docx-xml", "docx"
    elif ext in (".md", ".txt", ".markdown"):
        text, method, kind = path.read_text(encoding="utf-8", errors="replace"), "plain", "text"
    else:
        out({"ok": False, "error": f"Unsupported file type {ext}. Use PDF, DOCX or Markdown."}, 2)
    flags, nwords = flags_for(text, layout, pages, path, kind)
    return {"ok": True, "file": str(path), "method": method, "pages": pages, "words": nwords,
            "flags": flags, "text": text.replace("\f", "\n").strip()}


# ---------------------------------------------------------------- verify-quotes

TRANS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2010": "-", "\u2011": "-", "\u2013": "-",
                       "\u2014": "-", "\u2212": "-", "\u00a0": " ", "\u2022": " ", "\u25cf": " ",
                       "\u25aa": " ", "*": " ", "_": " ", "`": " ", "#": " "})


def norm(s):
    s = unicodedata.normalize("NFKC", s).translate(TRANS).lower()
    return re.sub(r"\s+", " ", s).strip(" .,;:-")


def collect_quotes(obj, found):
    """Pull every `quote` and `before` string out of whatever JSON shape the panel produced."""
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, list):
        for x in obj:
            collect_quotes(x, found)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("quote", "before") and isinstance(v, str) and v.strip():
                found.append(v)
            elif isinstance(v, (dict, list)):
                collect_quotes(v, found)
    return found


def verify_quotes(resume_path, quotes_path):
    rp = Path(resume_path)
    text = extract(rp)["text"] if rp.suffix.lower() in (".pdf", ".docx") else rp.read_text(encoding="utf-8")
    hay = norm(text)
    quotes = collect_quotes(json.loads(Path(quotes_path).read_text(encoding="utf-8")), [])
    matched, unmatched = [], []
    for q in dict.fromkeys(quotes):  # dedupe, keep order
        (matched if norm(q) and norm(q) in hay else unmatched).append(q)
    return {"ok": not unmatched, "checked": len(matched) + len(unmatched),
            "matched": matched, "unmatched": unmatched}


# ---------------------------------------------------------------- render

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    """Enough Markdown for a resume: headings, bullets, paragraphs, bold, italic, links."""
    body, para, in_list = [], [], False
    def flush():
        nonlocal para
        if para:
            body.append(f"<p>{inline(' '.join(para))}</p>")
            para = []
    for line in md.splitlines():
        s = line.strip()
        m = re.match(r"^(#{1,3})\s+(.*)", s)
        bullet = re.match(r"^[-*+]\s+(.*)", s)
        if not bullet and in_list:
            body.append("</ul>")
            in_list = False
        if not s:
            flush()
        elif m:
            flush()
            n = len(m.group(1))
            body.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif bullet:
            flush()
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{inline(bullet.group(1))}</li>")
        elif re.fullmatch(r"-{3,}|\*{3,}", s):
            flush()
        else:
            para.append(s)
    flush()
    if in_list:
        body.append("</ul>")
    return "\n".join(body)


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Resume</title><style>
@page {{ size: {paper}; margin: 0.6in 0.7in; }}
body {{ font-family: Arial, Helvetica, "Liberation Sans", sans-serif; font-size: 10.5pt; line-height: 1.35; color: #000; }}
h1 {{ font-size: 18pt; margin: 0 0 4pt; }}
h2 {{ font-size: 12pt; letter-spacing: .02em; border-bottom: 1px solid #000; margin: 12pt 0 4pt; padding-bottom: 2pt; }}
h3 {{ font-size: 10.5pt; margin: 8pt 0 2pt; }}
p {{ margin: 0 0 4pt; }}
ul {{ margin: 0 0 4pt; padding-left: 16pt; }}
li {{ margin: 0 0 2pt; }}
a {{ color: #000; text-decoration: none; }}
</style></head><body>
{body}
</body></html>"""


def chrome_path():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(p):
            return p
    return None


def html_to_pdf(page_html, out_pdf):
    """Try weasyprint, then pandoc, then headless Chrome/Edge. Returns the engine name or None."""
    out_pdf = Path(out_pdf).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    try:
        from weasyprint import HTML
        HTML(string=page_html).write_pdf(str(out_pdf))
        return "weasyprint"
    except Exception:
        pass
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "resume.html"
        src.write_text(page_html, encoding="utf-8")
        if shutil.which("pandoc"):
            r = run(["pandoc", str(src), "-o", str(out_pdf)])
            if r.returncode == 0 and out_pdf.exists():
                return "pandoc"
        chrome = chrome_path()
        if chrome:
            if out_pdf.exists():
                out_pdf.unlink()
            run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                 "--print-to-pdf-no-header", f"--user-data-dir={Path(td) / 'profile'}",
                 "--virtual-time-budget=2000", f"--print-to-pdf={out_pdf}", src.as_uri()])
            if out_pdf.exists() and out_pdf.stat().st_size > 0:
                return "chrome"
    return None


def render(src, out_pdf, paper):
    src = Path(src)
    text = src.read_text(encoding="utf-8")
    page = text if src.suffix.lower() in (".html", ".htm") else PAGE.format(paper=paper, body=md_to_html(text))
    engine = html_to_pdf(page, out_pdf)
    if not engine:
        return {"ok": False, "error": "No PDF renderer found.",
                "install": ["pip install weasyprint", "or install Google Chrome / Microsoft Edge",
                            "or install pandoc with a PDF engine"],
                "fallback": f"Use the Markdown as-is: {src}"}
    return {"ok": True, "engine": engine, "out": str(Path(out_pdf).resolve())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("file")
    v = sub.add_parser("verify-quotes"); v.add_argument("resume"); v.add_argument("quotes")
    r = sub.add_parser("render"); r.add_argument("src"); r.add_argument("out")
    r.add_argument("--paper", default="letter", choices=["letter", "a4"])
    a = ap.parse_args()
    if a.cmd == "extract":
        out(extract(a.file))
    if a.cmd == "verify-quotes":
        out(verify_quotes(a.resume, a.quotes))
    if a.cmd == "render":
        res = render(a.src, a.out, a.paper)
        out(res, 0 if res["ok"] else 2)


if __name__ == "__main__":
    main()
