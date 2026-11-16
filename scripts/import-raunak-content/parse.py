import sys, json, re, os, zipfile
import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

src, outjson, mediadir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(mediadir, exist_ok=True)
d = docx.Document(src)
numbering = d.part.numbering_part.element if d.part.numbering_part is not None else None

def num_fmt(numId, ilvl):
    if numbering is None: return "bullet"
    for n in numbering.findall(qn("w:num")):
        if n.get(qn("w:numId")) == str(numId):
            aid = n.find(qn("w:abstractNumId")).get(qn("w:val"))
            for a in numbering.findall(qn("w:abstractNum")):
                if a.get(qn("w:abstractNumId")) == aid:
                    for l in a.findall(qn("w:lvl")):
                        if l.get(qn("w:ilvl")) == str(ilvl):
                            f = l.find(qn("w:numFmt"))
                            return f.get(qn("w:val")) if f is not None else "bullet"
    return "bullet"

rels = d.part.rels
def hyperlink_url(h):
    rid = h.get(qn("r:id"))
    return rels[rid].target_ref if rid and rid in rels else None

def run_text(r):
    t = ""
    for c in r.iter():
        if c.tag == qn("w:t"): t += c.text or ""
        elif c.tag == qn("w:tab"): t += " "
        elif c.tag == qn("w:br"): t += "\n"
    return t

def run_bold(r):
    rpr = r.find(qn("w:rPr"))
    if rpr is None: return False
    b = rpr.find(qn("w:b"))
    if b is None: return False
    return b.get(qn("w:val")) not in ("0", "false")

def inline(p):
    """markdown-ish string: **bold**, [text](url). returns (text, all_bold)"""
    parts = []
    def add(txt, bold, url=None):
        if txt == "": return
        parts.append((txt, bold, url))
    for ch in p._p:
        if ch.tag == qn("w:r"): add(run_text(ch), run_bold(ch))
        elif ch.tag == qn("w:hyperlink"):
            u = hyperlink_url(ch)
            for r in ch.findall(qn("w:r")): add(run_text(r), run_bold(r), u)
    # merge adjacent
    out = ""; allbold = True; any_text = False
    for txt, bold, url in parts:
        if txt.strip() == "":
            out += txt; continue
        any_text = True
        if not bold: allbold = False
        seg = txt
        if url: seg = f"[{seg.strip()}]({url})" + (" " if seg.endswith(" ") else "")
        out += f"**{seg}**" if (bold and not url) else seg
    out = out.replace("****", "")
    return out, (allbold and any_text), any_text

img_n = 0
def images_of(p):
    global img_n
    res = []
    for blip in p._p.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if rid and rid in rels:
            part = rels[rid].target_part
            img_n += 1
            ext = os.path.splitext(part.partname)[1] or ".jpeg"
            name = f"{os.path.basename(src)[:8]}_{os.path.basename(str(part.partname))}"
            open(os.path.join(mediadir, name), "wb").write(part.blob)
            res.append(name)
    return res

blocks = []
def body_iter():
    for ch in d.element.body.iterchildren():
        if ch.tag == qn("w:p"): yield Paragraph(ch, d)
        elif ch.tag == qn("w:tbl"): yield Table(ch, d)

for el in body_iter():
    if isinstance(el, Table):
        rows = []
        for r in el.rows:
            cells = []
            seen = set()
            for c in r.cells:
                if id(c._tc) in seen: continue
                seen.add(id(c._tc))
                txt = " ".join(inline(p)[0].strip() for p in c.paragraphs if inline(p)[0].strip())
                cells.append(txt.replace("****", ""))
            rows.append(cells)
        blocks.append({"t": "table", "rows": rows})
        continue
    p = el
    imgs = images_of(p)
    for im in imgs: blocks.append({"t": "img", "file": im})
    text, allbold, anytext = inline(p)
    plain = re.sub(r"\*\*|\[|\]\([^)]*\)", "", text).strip()
    if not plain: continue
    ppr = p._p.find(qn("w:pPr"))
    numpr = ppr.find(qn("w:numPr")) if ppr is not None else None
    ind = ppr.find(qn("w:ind")) if ppr is not None else None
    style = p.style.name if p.style is not None else ""
    if numpr is not None and numpr.find(qn("w:numId")) is not None and numpr.find(qn("w:numId")).get(qn("w:val")) != "0":
        nid = numpr.find(qn("w:numId")).get(qn("w:val"))
        il = numpr.find(qn("w:ilvl")); il = int(il.get(qn("w:val"))) if il is not None else 0
        fmt = num_fmt(nid, il)
        blocks.append({"t": "li", "kind": "ol" if fmt in ("decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman") else "ul", "lvl": il, "text": text.strip()})
        continue
    if style.startswith("Heading"):
        blocks.append({"t": "h", "text": plain, "style": style}); continue
    left = int(ind.get(qn("w:left")) or 0) if ind is not None and ind.get(qn("w:left")) else 0
    if allbold and len(plain) < 160 and "\n" not in plain:
        blocks.append({"t": "h", "text": plain}); continue
    kind = "note" if left >= 700 and not re.match(r"^\d+[\).]", plain) else "p"
    blocks.append({"t": kind, "text": text.strip()})

json.dump(blocks, open(outjson, "w"), ensure_ascii=False, indent=0)
from collections import Counter
print(Counter(b["t"] for b in blocks), "images", img_n)
