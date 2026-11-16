import json, re, os, hashlib
from PIL import Image
P = "/home/claude/project/medtrip-connect-main/"
MEDIA = "/tmp/claude-0/nov9/media_h/"
b = json.load(open("/tmp/claude-0/nov9/hosp.json"))
starts = [0,68,140,267,335,384,440,516,603,692,764,831,900,975,1018,1058,len(b)]
SLUG = ["artemis-hospitals","apollo-main-hospital-greams-road","apollo-indraprastha-hospitals","asian-institute-of-medical-sciences","zemya-ivf","nova-ivf-fertility","phs-fertility-centre-kolkata","amrita-hospitals","fortis-escorts-heart-institute","fortis-hospital-kolkata","desun-hospital","tx-hospitals","kauvery-hospitals","manipal-hospitals-siliguri","p-and-o-international-artificial-limb-centre","sharp-sight-eye-hospitals"]
DEPT = {"Cardiology":"cardiology","Orthopedic & Joint Replacement":"orthopedic-and-joint-replacement","Neurology":"neurology","Haemato Oncology & BMT":"haemato-oncology","Oncology":"oncology","Spine & Scoliosis Surgery":"spine-and-scoliosis-surgery","Opthamology":"ophthalmology","Urology & Kidney Transplant":"urology-and-kidney-transplant","Liver Transplant & GI & HPB Surgery":"liver-transplant-gi-and-hpb-surgery","Cardiac Thoracic & Vascular Surgery":"cardio-thoracic-and-vascular-surgery","Cosmetic & Plastic Surgery":"cosmetic-and-plastic-surgery","ENT & Cochlear Implant":"ent-and-cochlear-implant","General & Minimally Invasive Surgery":"general-and-laparoscopic-surgery","Gastroenterology":None,"Dermatology & Cosmetology":"dermatology-and-cosmetology","Dentistry":"dentistry","Obstetrics & Gynaecology":"obstetrics-and-gynaecology","Neurointerventional Surgery":"neurointerventional-surgery","Medical Oncology":None,"Surgical Oncology":None,"Gynaecological Oncology":None,"Nephrology":"nephrology"}
DASH = lambda t: re.sub(r"\s*[–—]\s*", lambda m: " - " if m.group(0).strip()!=m.group(0) else "-", t)
def clean(t):
    t = re.sub(r"\[([^\]]*)\]\((?:https?://)[^)]*\)", r"\1", t)        # drop google-search hyperlinks, keep text
    t = re.sub(r"\*\*\s*\*\*", "", t); t = t.replace(" "," ")
    t = re.sub(r"[ \t]+"," ",t).strip()
    return DASH(t)
def strip_b(t): return re.sub(r"\*\*","",t).strip()
outdir = P+"public/hospitals/gallery/"; os.makedirs(outdir, exist_ok=True); os.makedirs(P+"public/hospitals/accreditation", exist_ok=True)
seen = {}
def to_webp(f, dst):
    im = Image.open(MEDIA+f).convert("RGB"); w,h = im.size
    if max(w,h) > 1200: im.thumbnail((1200,1200)); w,h = im.size
    im.save(dst, "WEBP", quality=82, method=6); return w,h
profiles = {}; flags = []; imgstat = []
for hi,(a,z) in enumerate(zip(starts,starts[1:])):
    s = b[a:z]; slug = SLUG[hi]; docname = s[0]["text"]
    pr = dict(docName=docname, established=None, beds=None, type=None, docLocation=None, address=None, accreditation=[], blocks=[], gallery=[])
    # ---- facts
    for x in s:
        t = x.get("text","")
        tt = strip_b(t)
        m = re.match(r"LOCATION:\s*(\S.*)$", tt)
        if m and x["t"]=="h": pr["docLocation"] = m.group(1).strip().title()
        m = re.match(r"ESTABLISHED:\s*(\S.*)$", tt)
        if m: pr["established"] = m.group(1).strip()
        m = re.match(r"NUMBER OF BEDS\s*:\s*(.*)$", tt, re.I)
        if m: pr["beds"] = m.group(1).strip()
        if x["t"]=="h" and tt in ("SUPER SPECIALITY","MULTI SPECIALITY"): pr["type"] = tt.title()
        m = re.match(r"(?:HOSPITAL )?ADDRESS\s*:\s*(\S.*)$", tt, re.I|re.S)
        if m and x["t"]=="p": pr["address"] = DASH(re.sub(r"\s+"," ",m.group(1)).strip())
    for i,x in enumerate(s):
        if x["t"]=="h" and strip_b(x["text"])=="HOSPITAL ADDRESS" and i+1<len(s) and s[i+1]["t"]=="p": pr["address"] = clean(s[i+1]["text"])
    # accreditation logos (image2 = JCI, image3 = NABH) listed under ACCREDITATION
    acc=False
    for x in s:
        if x["t"]=="h": acc = strip_b(x["text"]).startswith("ACCREDITATION")
        elif x["t"]=="img" and acc:
            if x["file"].endswith("image2.jpeg"): pr["accreditation"].append("JCI")
            if x["file"].endswith("image3.jpeg"): pr["accreditation"].append("NABH")
        elif x["t"]!="h": acc = False if x["t"]!="img" else acc
    # ---- body blocks: from ABOUT HOSPITAL (or SERVICES for P&O) on
    start = next(i for i,x in enumerate(s) if x["t"]=="p" and strip_b(x.get("text","")).upper().startswith("ABOUT HOSPITAL"))
    blocks=[]; i=start; in_images=False; in_dept=False; dept_items=[]
    def flush():
        global dept_items
    while i < len(s):
        x = s[i]; t = x.get("text",""); tt = strip_b(t); i += 1
        up = tt.upper()
        if x["t"]=="img": continue
        if x["t"]=="h" and up.startswith("IMAGES"): in_images=True; continue
        if x["t"]=="h" and up.startswith(("AWARDS","HOSPITAL ADDRESS")): in_images=False
        if in_images: continue
        if "OUR EXPERIENCED DOCTORS" in up or up.startswith("BANNER IMAGE") or "GIVE GOOGLE MAP" in up or re.match(r"LOCATION\*?\*?\s*:\s*\(GIVE", up): continue
        if re.match(r"(HOSPITAL )?ADDRESS\s*:", up) or up.startswith("HOSPITAL ADDRESS") or up=="HOSPITAL ADDRESS" or (blocks and False): 
            if up=="HOSPITAL ADDRESS": i += 1   # skip the address paragraph (kept as fact)
            continue
        if x["t"]=="p":
            t2 = re.sub(r"^\*\*ABOUT HOSPITAL\*?\*?\s*:\s*\*?\*?\s*","",clean(t),flags=re.I)
            if t2: blocks.append({"t":"p","text":t2})
        elif x["t"]=="h":
            h = tt
            if h in DEPT:
                if blocks and blocks[-1]["t"]=="list" and blocks[-1].get("_dept"): blocks[-1]["items"].append({"text": h})
                else: blocks.append({"t":"list","ordered":False,"items":[{"text":h}],"_dept":True})
                continue
            if h.isupper() or h.endswith(":"): h = h.rstrip(":").strip().capitalize().replace(" and "," and ")
            lvl = 2 if (strip_b(x["text"]).isupper() or strip_b(x["text"]).endswith(":") or h in ("Additional medical services","Support services")) else 3
            blocks.append({"t":"h","text":DASH(h),"lvl":lvl})
        elif x["t"]=="li":
            d = x.get("depth",0) or 0
            item = {"text": clean(t)}
            if blocks and blocks[-1]["t"]=="list" and not blocks[-1].get("_dept"):
                lst = blocks[-1]["items"]
                if d==0: lst.append(item)
                else:
                    if "children" not in lst[-1]: lst[-1]["children"]=[]
                    lst[-1]["children"].append(item)
            else: blocks.append({"t":"list","ordered":False,"items":[item]})
        elif x["t"]=="table":
            rows = [[clean(c) for c in r] for r in x["rows"]]
            head = rows[0]; blocks.append({"t":"table","head":[strip_b(c) for c in head],"rows":rows[1:]})
    # dept link lists -> remember slugs
    for bl in blocks:
        if bl.get("_dept"):
            del bl["_dept"]
            for it in bl["items"]:
                if DEPT.get(it["text"]): it["href"] = "/services/"+DEPT[it["text"]]
    # runs of short plain paragraphs (a typed-out list) -> a real list
    out=[]; run=[]
    def endrun():
        global run
        if len(run)>=3: out.append({"t":"list","ordered":False,"items":[{"text":r["text"]} for r in run]})
        else: out.extend(run)
        run=[]
    for bl in blocks:
        if bl["t"]=="p" and len(bl["text"])<80 and not bl["text"].endswith((".",":")): run.append(bl)
        else: endrun(); out.append(bl)
    endrun(); blocks=out
    # headings with nothing under them (e.g. an empty "Awards and recognition")
    blocks=[bl for k,bl in enumerate(blocks) if not (bl["t"]=="h" and (k+1==len(blocks) or blocks[k+1]["t"]=="h"))]
    for bl in blocks:
        if bl["t"]=="list":
            for it in bl["items"]:
                if it["text"]=="Opthamology": it["text"]="Ophthalmology"
    if pr["beds"]:
        pr["beds"]=re.sub(r"\s*BEDS\s*$","",pr["beds"]).strip() or None
    if pr["established"] and not re.fullmatch(r"\d{4}",pr["established"]): flags.append((slug,"established incomplete: "+pr["established"])); pr["established"]=None
    if not pr["beds"]: flags.append((slug,"beds missing"))
    if not pr["address"]: flags.append((slug,"address missing"))
    pr["blocks"] = blocks
    # ---- images
    n=0
    for k,x in enumerate(s):
        if x["t"]!="img": continue
        f = x["file"]
        if f.endswith(("image2.jpeg","image3.jpeg")) and False: pass
        im = Image.open(MEDIA+f); w,h = im.size
        why=None
        if (w,h) in ((250,250),(365,299)): why="accreditation logo (rendered as badge)"
        elif (w,h)==(1377,520): why="Google Maps screenshot"
        elif w<400: why=f"too small ({w}px)"
        elif slug.startswith("p-and-o") and f.endswith("image73.jpeg"): why="unidentified personal portrait"
        else:
            hsh = hashlib.md5(im.convert("L").resize((16,16)).tobytes()).hexdigest()
            if hsh in seen.setdefault(slug,set()): why="duplicate of another photo"
            seen[slug].add(hsh)
        imgstat.append((slug,f,w,h,why))
        if why: continue
        n+=1; dst=f"{outdir}{slug}-{n}.webp"; ww,hh = to_webp(f,dst)
        pr["gallery"].append({"src":f"/hospitals/gallery/{slug}-{n}.webp","w":ww,"h":hh})
    profiles[slug] = pr
# accreditation logos
for nm,f in (("jci","image2.jpeg"),("nabh","image3.jpeg")):
    to_webp("e4bc1145_"+f, P+f"public/hospitals/accreditation/{nm}.webp")
json.dump(profiles, open("/tmp/claude-0/nov9/profiles.json","w"), ensure_ascii=False, indent=1)
print(flags); json.dump(imgstat, open("/tmp/claude-0/nov9/imgstat.json","w"))
for s_,p in profiles.items(): print(s_, p["established"], p["beds"], p["type"], p["docLocation"], "|", (p["address"] or "-")[:50], "| acc", p["accreditation"], "| blocks", len(p["blocks"]), "gallery", len(p["gallery"]))
