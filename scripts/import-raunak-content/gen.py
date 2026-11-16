import json, re, os, sys
from PIL import Image
MAIN = json.load(open("/tmp/claude-0/raunak/main.json"))
SUB = json.load(open("/tmp/claude-0/raunak/sub.json"))
PROJ = "/home/claude/project/medtrip-connect-main"
MEDIA_MAIN = "/tmp/claude-0/raunak/media_main"; MEDIA_SUB = "/tmp/claude-0/raunak/media_sub"

# ---------- helpers ----------
def clean(t):
    t = re.sub(r"\s*\[(?:\[\d+\]\([^)]*\)[,\s]*)+\]", "", t)          # [[1](url)] citation artefacts
    t = re.sub(r"\[\]\]\([^)]*\)", "", t)               # []](url)
    t = re.sub(r"\[\s*\]\([^)]*\)", "", t)
    t = t.replace(" ", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\*\*\s*\*\*", " ", t)
    t = re.sub(r"\*\*(\s+)\*\*", r"\1", t)
    return t.strip()
plain = lambda t: re.sub(r"\*\*|\[([^\]]*)\]\([^)]*\)", r"\1", t).strip()

HOSP_MAP = [  # (regex on upper-cased name, slug)
    (r"KAUVERY", "kauvery-hospitals"), (r"FORTIS ESCORTS HEART", "fortis-escorts-heart-institute"),
    (r"DESUN", "desun-hospital"), (r"APOLLO CANCER", "apollo-super-speciality-hospitals-cancer-centre"),
    (r"APOLLO MAIN|APOLLO HOSPITALS?, CHENNAI|APOLLO HOSPITAL, CHENNAI", "apollo-main-hospital-greams-road"),
    (r"INDRAPR[A-Z]*STHA", "apollo-indraprastha-hospitals"), (r"ARTEMIS", "artemis-hospitals"),
    (r"^TX ", "tx-hospitals"), (r"SHARP SIGHT", "sharp-sight-eye-hospitals"), (r"ZEMYA", "zemya-ivf"),
    (r"PHS FERTILITY", "phs-fertility-centre-kolkata"), (r"NOVA IVF", "nova-ivf-fertility"),
]
def hosp_slug(name):
    u = re.sub(r"\s+", " ", name.upper().replace(" ,", ",")).strip()
    for rx, s in HOSP_MAP:
        if re.search(rx, u): return s
    return None
review = {"hospital_name_issues": [], "unmapped_hospitals": []}

def hospitals_from(names, where):
    out = []; raw = []
    for n in names:
        n = plain(n); raw.append(n)
        s = hosp_slug(n)
        if not s: review["unmapped_hospitals"].append((where, n)); continue
        if s not in out: out.append(s)
        else: review["hospital_name_issues"].append((where, f"'{n}' repeats an earlier entry (shown once)"))
    return out, raw

# ---------- convert blocks ----------
COSTLINE = re.compile(r"^(the )?cost of .{3,200}?(usd|\$)", re.I)
def convert(blocks, ctx):
    """blocks -> content blocks; returns (blocks, hospitals_raw, hospitals_slugs, doctor_note)"""
    out = []; i = 0; hosp_raw = []; doc_note = None; hosp_title = None
    n = len(blocks)
    pending_imgs = []
    def flush_imgs(label):
        for f in pending_imgs: out.append({"t": "img", "file": f, "alt": (plain(label)[:110] + " - illustration") if label else "Illustration"})
        pending_imgs.clear()
    while i < n:
        x = blocks[i]; t = x["t"]
        if t == "img": pending_imgs.append(x["file"]); i += 1; continue
        txt = clean(x.get("text", "")) if "text" in x else ""
        pl = plain(txt)
        # hospital / doctor placeholders
        if t in ("p", "h") and re.match(r"^(TOP|BEST) HOSPITALS", pl, re.I):
            hosp_title = re.sub(r"^(TOP )+HOSPITALS FOR (TOP HOSPITALS FOR )?", "", pl, flags=re.I).strip()
            j = i + 1; names = []
            while j < n and blocks[j]["t"] == "p" and not re.match(r"^(TOP|BEST) DOCTORS", plain(blocks[j]["text"]), re.I):
                names.append(blocks[j]["text"]); j += 1
            hosp_raw = names; i = j; continue
        if t in ("p", "h") and re.match(r"^(TOP|BEST) DOCTORS", pl, re.I):
            doc_note = pl; i += 1; continue
        if t == "h" and pl.startswith("(Hyperlink"): i += 1; continue
        if t == "table":
            rows = [[clean(c) for c in r] for r in x["rows"]]
            rows = [r for r in rows if any(plain(c) for c in r)]
            head = None
            if rows and all(c.startswith("**") or c == "" for c in rows[0]) and any(c for c in rows[0]):
                head = [plain(c) for c in rows[0]]; rows = rows[1:]
            elif rows and re.match(r"^(procedure|treatment|type of|surgery|eye procedure|programme|category|orthopaedic)", plain(rows[0][0]), re.I):
                head = [plain(c) for c in rows[0]]; rows = rows[1:]
            rows = [[plain(c) for c in r] for r in rows]
            out.append({"t": "table", "head": head, "rows": rows}); i += 1; continue
        if t == "li":
            if pending_imgs: flush_imgs(plain(clean(x["text"])))
            # collect consecutive list items
            items = []; j = i
            while j < n and blocks[j]["t"] == "li":
                items.append(blocks[j]); j += 1
            # group by ordered/unordered at level 0 boundaries
            def build(seq):
                root = []; stack = [(-1, root, None)]
                for it in seq:
                    node = {"text": clean(it["text"])}
                    while stack and stack[-1][0] >= it["lvl"]: stack.pop()
                    parent = stack[-1][1]
                    if stack[-1][2] is not None and stack[-1][0] >= 0: pass
                    parent.append(node)
                    node["children"] = []
                    stack.append((it["lvl"], node["children"], node))
                def trim(ns):
                    for nn in ns:
                        if nn["children"]: trim(nn["children"])
                        else: del nn["children"]
                trim(root); return root
            k = 0
            while k < len(items):
                kind = items[k]["kind"]; m = k
                while m < len(items) and (items[m]["kind"] == kind or items[m]["lvl"] > 0): m += 1
                tree = build(items[k:m]); tree = [t_ for t_ in tree if plain(t_["text"])]
                if tree: out.append({"t": "list", "ordered": kind == "ol", "items": tree})
                k = m
            i = j; continue
        if t == "h":
            level = 2 if (pl.isupper() or pl.startswith("Category") or re.match(r"^why ", pl, re.I)) else 3
            if re.match(r"^\d+[\.\)]", pl): level = 3
            if COSTLINE.match(pl) or re.match(r"^cost of ", pl, re.I):
                out.append({"t": "cost", "text": txt}); i += 1; continue
            out.append({"t": "h", "text": pl, "lvl": level}); flush_imgs(pl); i += 1; continue
        if t == "note":
            out.append({"t": "note", "text": txt}); i += 1; continue
        if t == "p":
            if re.match(r"^(PROCEDURE TIME DURATION|MINIMUM COST|MAXIMUM COST|LENGTH OF STAY IN HOSPITAL|LENGTH OF STAY IN INDIA)\s*:", pl, re.I):
                label, _, val = pl.partition(":")
                if out and out[-1]["t"] == "facts": out[-1]["items"].append([label.strip().title().replace("In India","in India").replace("In Hospital","in Hospital"), val.strip()])
                else: out.append({"t": "facts", "items": [[label.strip().title().replace("In India","in India").replace("In Hospital","in Hospital"), val.strip()]]})
                i += 1
                while i < n and blocks[i]["t"] == "p":
                    nx = plain(clean(blocks[i]["text"]))
                    if re.match(r"^[A-Za-z ]{3,20}\s*:\s*\S", nx) and len(nx) < 45 and not re.match(r"^(PROCEDURE|MINIMUM|MAXIMUM|LENGTH)", nx, re.I):
                        it = out[-1]["items"][-1]
                        it[1] = (it[1] + "; " if it[1] else "") + re.sub(r"\s*:\s*", ": ", nx, count=1)
                        i += 1
                    else: break
                continue
            if COSTLINE.match(pl) and len(pl) < 260:
                out.append({"t": "cost", "text": txt}); i += 1; continue
            out.append({"t": "p", "text": txt})
            if pending_imgs: flush_imgs(re.sub(r"^\d+[\.\)]\s*", "", pl))
            i += 1; continue
        i += 1
    # images that never found a following heading: attach as-is at the end of their position
    flush_imgs("Illustration")
    return out, hosp_raw, hosp_title, doc_note

# ---------- images ----------
WITHHELD = {  # image number in treatment.docx -> reason (third-party branding / other language / watermark / redaction)
    8: "German caption ('Meniskusnaht')", 11: "Turkish caption ('Civi Ile Kirik Tespiti')", 12: "'MEDICAL' vendor watermark",
    13: "redacted patient/case label in the image", 21: "French caption ('Resultat de chirurgie scoliose')",
    28: "Cleveland Clinic copyright mark", 29: "third-party logo mark", 32: "Medicover Hospitals branding",
    37: "Mayo Foundation copyright mark", 48: "Mayo Clinic copyright mark", 51: "Healthline branding",
    53: "Mayo Foundation copyright mark", 57: "Medicover Hospitals branding", 58: "Mayo Foundation copyright mark",
    59: "Elekta product branding", 60: "CyberKnife / Accuray product branding", 62: "small copyright mark (unreadable)",
    65: "Mayo Foundation copyright mark",
}
os.makedirs(f"{PROJ}/content-review/images", exist_ok=True)
withheld_report = []
def place_image(fname, scope, slug_hint, idx):
    num = int(re.search(r"image(\d+)", fname).group(1))
    src = os.path.join(MEDIA_MAIN if fname.startswith("4761475e") else MEDIA_SUB, fname)
    if fname.startswith("4761475e") and num in WITHHELD:
        dst = f"{PROJ}/content-review/images/department-doc-image{num}.jpeg"
        open(dst, "wb").write(open(src, "rb").read())
        withheld_report.append((f"department-doc-image{num}.jpeg", scope, WITHHELD[num]))
        return None
    d = f"{PROJ}/public/content/{scope}"; os.makedirs(d, exist_ok=True)
    name = f"{slug_hint}-{idx}.webp"
    im = Image.open(src).convert("RGB")
    if im.width > 960: im = im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS)
    im.save(f"{d}/{name}", "WEBP", quality=80)
    return f"/content/{scope}/{name}", im.width, im.height

def finalize_images(blocks, scope):
    res = []; k = 0
    for b in blocks:
        if b["t"] == "img":
            k += 1
            r = place_image(b.pop("file"), scope, scope, k)
            if r: b["src"], b["w"], b["h"] = r; res.append(b)
        else: res.append(b)
    return res

# ---------- departments ----------
DEPTS = [
 ("cardiology", 0, 47), ("oncology", 47, 111), ("spine-and-scoliosis-surgery", 111, 154), ("ophthalmology", 154, 199),
 ("urology-and-kidney-transplant", 199, 242), ("orthopedic-and-joint-replacement", 242, 486),
 ("liver-transplant-gi-and-hpb-surgery", 486, 628), ("cosmetic-and-plastic-surgery", 628, 664), ("ent-and-cochlear-implant", 664, 689),
 ("dentistry", 689, 703), ("ivf-and-reproductive-medicine", 703, 738), ("obstetrics-and-gynaecology", 738, 756),
 ("neurology", 756, 887), ("pulmonology", 887, 925), ("general-and-laparoscopic-surgery", 925, 926),
 ("prosthetic-and-artificial-body-parts", 926, 927),
]
# cost pages
PAGES = [
 dict(slug="angioplasty", name="Angioplasty", h1="Cost of Angioplasty in India", a=1, b=73, docs=["cardiology"], parent="cardiology", show=["cardiology","cardio-thoracic-and-vascular-surgery"],
      card="The cost of angioplasty in India is around 2500 USD onwards.", m=r"cost of angioplasty in india"),
 dict(slug="cabg-heart-bypass", name="CABG / Heart Bypass", h1="Cost of CABG (Bypass) Surgery in India", a=73, b=137, docs=["cardiology"], parent="cardiology", show=["cardiology","cardio-thoracic-and-vascular-surgery"],
      card="The cost of Bypass CABG in India is around 4000 USD onwards.", m=r"cost of bypass cabg"),
 dict(slug="asd-vsd-repair", name="ASD / VSD Repair", h1="Cost of ASD / VSD Repair Surgery in India", a=137, b=199, docs=["cardiology"], parent="cardiology", show=["cardiology","cardio-thoracic-and-vascular-surgery","pediatric-cardiac-care"],
      card="The cost of ASD/VSD defect repair surgery in India around 7000 USD onwards.", m=r"cost of asd/vsd defect repair"),
 dict(slug="cervical-cancer", name="Cervical Cancer", h1="Cost of Cervical Cancer Treatment in India", a=199, b=265, docs=["oncology"], parent="oncology", show=["oncology"],
      card="The cost of Cervical cancer in India is around 5000 USD onwards.", m=r"cost of cervical cancer in india"),
 dict(slug="breast-cancer", name="Breast Cancer", h1="Cost of Breast Cancer Treatment in India", a=265, b=331, docs=["oncology"], parent="oncology", show=["oncology"],
      card="The cost of breast cancer treatment in India is around 5500 USD onwards.", m=r"cost of breast cancer treatment"),
 dict(slug="bone-marrow-transplant", name="Bone Marrow Transplant", h1="Cost of Bone Marrow Transplant in India", a=331, b=419, docs=["haemato-oncology","oncology"], parent="oncology", show=["oncology","haemato-oncology"],
      card="The cost of bone marrow transplant in India starts from 14000 USD and varies as per patient condition and the type of transplant (Autologous or Allogenic).", m=None),
 dict(slug="spinal-fusion", name="Spinal Fusion", h1="Cost of Spinal Fusion Surgery in India", a=419, b=477, docs=["spine-and-scoliosis-surgery"], parent="spine-and-scoliosis-surgery", show=["spine-and-scoliosis-surgery","orthopedic-and-joint-replacement"],
      card="The cost of spinal fusion in India is 7000 USD", m=r"cost of (lumbar )?spinal fusion"),
 dict(slug="knee-replacement", name="Knee Replacement", h1="Cost of Knee Replacement Surgery in India", a=477, b=537, docs=["orthopedic-and-joint-replacement"], parent="orthopedic-and-joint-replacement", show=["orthopedic-and-joint-replacement"],
      card="Cost of knee replacement in India starts US $4000.", m=r"cost of knee replacement in india starts us \$4000"),
 dict(slug="hip-replacement", name="Hip Replacement", h1="Cost of Hip Replacement Surgery in India", a=537, b=609, docs=["orthopedic-and-joint-replacement"], parent="orthopedic-and-joint-replacement", show=["orthopedic-and-joint-replacement"],
      card="Cost of hip replacement in India starts US $5500.", m=r"cost of total hip replacement"),
 dict(slug="liver-transplant", name="Liver Transplant", h1="Cost of Liver Transplant in India", a=609, b=671, docs=["liver-transplant-gi-and-hpb-surgery"], parent="liver-transplant-gi-and-hpb-surgery", show=["liver-transplant-gi-and-hpb-surgery"],
      card="Cost of liver transplant surgery in India starts from US $15000", m=r"cost of liver transplant surgery"),
 dict(slug="ivf-treatment", name="IVF Treatment", h1="Cost of IVF Treatment in India", a=671, b=721, docs=["ivf-and-reproductive-medicine"], parent="ivf-and-reproductive-medicine", show=["ivf-and-reproductive-medicine"],
      card="The cost of IVF treatment in India starts from 2500 USD", m=r"cost of ivf treatment"),
 dict(slug="spinal-decompression-laminectomy", name="Spinal Decompression / Laminectomy", h1="Cost of Spinal Decompression / Laminectomy Surgery in India", a=721, b=779, docs=["spine-and-scoliosis-surgery"], parent="spine-and-scoliosis-surgery", show=["spine-and-scoliosis-surgery","orthopedic-and-joint-replacement"],
      card="The cost of spinal decompression/laminectomy in India is 2300 USD", m=r"laminectomy|laminotomy|spinal decompression"),
 dict(slug="brain-tumour-surgery", name="Brain Tumour Surgery", h1="Cost of Brain Tumour Surgery in India", a=779, b=len(SUB), docs=["neurosurgery","neurology"], parent="neurology", show=["neurology","neurosurgery","oncology"],
      card="The cost of brain tumour treatment in India is around 6500 USD.", m=r"brain tumou?rs? (surgery|treatment)"),
]
LINK_DEPTS = {  # which departments get inline links for which page (first matching cost line only)
 "angioplasty":["cardiology"],"cabg-heart-bypass":["cardiology"],"asd-vsd-repair":["cardiology"],"cervical-cancer":["oncology"],"breast-cancer":["oncology"],
 "spinal-fusion":["spine-and-scoliosis-surgery","orthopedic-and-joint-replacement"],"knee-replacement":["orthopedic-and-joint-replacement"],"hip-replacement":["orthopedic-and-joint-replacement"],
 "liver-transplant":["liver-transplant-gi-and-hpb-surgery"],"ivf-treatment":["ivf-and-reproductive-medicine"],
 "spinal-decompression-laminectomy":["neurology"],"brain-tumour-surgery":["neurology"],
}
link_log = []
dept_out = {}
for slug, a, b in DEPTS:
    seg = MAIN[a:b]
    title = plain(seg[0].get("text", "")) if seg and seg[0]["t"] == "h" else ""
    body = seg[1:]
    # IVF: hospital names are unlabeled at the end
    forced_hosp = None
    if slug == "ivf-and-reproductive-medicine":
        forced_hosp = [x["text"] for x in body[-3:]]; body = body[:-3]
    blocks, hraw, htitle, dnote = convert(body, slug)
    if forced_hosp: hraw = forced_hosp; htitle = "IVF & FERTILITY TREATMENT"
    hs, hraw_clean = hospitals_from(hraw, slug)
    blocks = finalize_images(blocks, slug)
    # inline links
    for p in PAGES:
        if not p["m"] or slug not in LINK_DEPTS.get(p["slug"], []): continue
        for bl in blocks:
            if bl["t"] in ("cost", "p", "note") and re.search(p["m"], plain(bl["text"]), re.I) and "href" not in bl and len(plain(bl["text"])) < 260 and re.match(r"^(the )?(\w+ ){0,4}cost|^the .{0,40}cost", plain(bl["text"]), re.I):
                bl["t"] = "cost" if bl["t"] != "note" else "cost"; bl["href"] = f"/treatment-cost/{p['slug']}"; link_log.append((slug, p["slug"], plain(bl["text"])[:90])); break
    HEADLINKS = {"orthopedic-and-joint-replacement": [(r"^\d+\. Total Knee Replacement", "knee-replacement"), (r"^\d+\. Total Hip Replacement", "hip-replacement"),
        (r"^\d+\. Laminectomy / Spinal Decompression", "spinal-decompression-laminectomy"), (r"^\d+\. Lumbar Spinal Fusion", "spinal-fusion")],
        "neurology": [(r"^8\. Spine and spinal cord", None)]}
    for rx, target in HEADLINKS.get(slug, []):
        for bl in blocks:
            if bl["t"] == "h" and target and re.search(rx, bl["text"]) and "href" not in bl:
                bl["href"] = f"/treatment-cost/{target}"; link_log.append((slug, target, "HEADING " + bl["text"])); break
    dept_out[slug] = dict(docTitle=title, blocks=blocks, hospitals=hs, hospitalsListed=hraw_clean,
                          hospitalsHeading=("Top hospitals for " + (htitle or "").lower().replace("&", "and")) if hs else None, doctorsNote=dnote)

# ---------- cost pages ----------
SUBFIX = {"asd-vsd-repair": ("cost of bypass surgery in India", "cost of ASD/VSD repair surgery in India"),
          "breast-cancer": ("cost of colon cancer treatment in India", "cost of breast cancer treatment in India"),
          "liver-transplant": ("cost of bypass surgery in India", "cost of liver transplant in India")}
HEADFIX = {"cabg-heart-bypass": [("FACTORS THAT AFFECT THE ANGIOPLASTY COST IN INDIA", "FACTORS THAT AFFECT THE CABG COST IN INDIA")]}
pages_out = {}; copy_fixes = []
for p in PAGES:
    seg = SUB[p["a"]:p["b"]]
    ban = clean(seg[0]["text"]); ban = re.sub(r"^\*+\.?\d*\.?\(\*+\s*\)?Header on banner image\)\s*", "", ban); ban = re.sub(r"^\*+", "", ban)
    ban = re.sub(r"\(\*\*Header on banner image\)", "", ban).replace("**", "").strip()
    m = re.match(r"^(.*?INDIA)\s*-\s*(.*)$", ban, re.S)
    sub = m.group(2).strip() if m else ""
    if p["slug"] in SUBFIX and SUBFIX[p["slug"]][0] in sub:
        sub = sub.replace(*SUBFIX[p["slug"]]); copy_fixes.append((p["slug"], "banner subtitle", SUBFIX[p["slug"]][0], SUBFIX[p["slug"]][1]))
    body = seg[1:]
    for bl in body:
        for old, new in HEADFIX.get(p["slug"], []):
            if bl.get("text") and plain(bl["text"]).upper() == old:
                bl["text"] = new; copy_fixes.append((p["slug"], "heading", old, new))
    blocks, hraw, htitle, dnote = convert(body, p["slug"])
    hs, hraw_clean = hospitals_from(hraw, p["slug"])
    blocks = finalize_images(blocks, "cost-" + p["slug"])
    # normalise headings
    ACR = [("asd","ASD"),("vsd","VSD"),("cabg","CABG"),("ivf","IVF"),("usd","USD"),("india","India"),("bmt","BMT"),("hla","HLA")]
    for bl in blocks:
        if bl["t"] == "h":
            t_ = bl["text"].strip().rstrip(":").strip()
            if t_.isupper(): t_ = t_.capitalize()
            t_ = re.sub(r"^(\d+[\.\)]\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t_)
            if t_[:1].islower(): t_ = t_[0].upper() + t_[1:]
            for a, b in ACR: t_ = re.sub(r"\b" + a + r"\b", b, t_, flags=re.I)
            t_ = re.sub(r"^WHAT IS THE COST OF", "What is the cost of", t_); t_ = t_.replace("IN India","in India")
            bl["text"] = t_
            bl["lvl"] = 2 if bl["lvl"] == 2 or t_.lower().startswith(("what is", "types", "factors", "pre surgery", "recovery", "why choose")) else 3
    # drop facts blocks with no values
    for bl in blocks:
        if bl["t"] == "facts": bl["items"] = [it for it in bl["items"] if it[1]]
    blocks = [b for b in blocks if not (b["t"] == "facts" and not b["items"])]
    pages_out[p["slug"]] = dict(slug=p["slug"], name=p["name"], h1=p["h1"], subtitle=sub, parent=p["parent"], doctorDepartments=p["docs"], showOn=p["show"],
        listCost=p["card"], blocks=blocks, hospitals=hs, hospitalsListed=hraw_clean, hospitalsHeading=("Best hospitals for " + p["name"]) if hs else None, doctorsHeading=dnote)

# DASHFIX: site-wide rule - plain hyphens only (typography change; figures untouched)
def _df(x):
    if isinstance(x, str): return re.sub(r"\s*[\u2013\u2014]\s*", lambda m: " - " if m.group(0).strip() != m.group(0) else "-", x)
    if isinstance(x, list): return [_df(i) for i in x]
    if isinstance(x, dict): return {k: (v if k in ("src","slug","t") else _df(v)) for k, v in x.items()}
    return x
dept_out = _df(dept_out); pages_out = _df(pages_out)
json.dump(dict(depts=dept_out, pages=pages_out), open("/tmp/claude-0/raunak/out.json", "w"), ensure_ascii=False, indent=1)
json.dump(dict(review=review, withheld=withheld_report, links=link_log, fixes=copy_fixes), open("/tmp/claude-0/raunak/report.json", "w"), ensure_ascii=False, indent=1)
print("depts", len(dept_out), "pages", len(pages_out))
for l in link_log: print("LINK", l)
print("fixes", copy_fixes)
print("review", review)
print("withheld", len(withheld_report))
