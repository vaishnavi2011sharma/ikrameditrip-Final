import json, re, os
from PIL import Image
P = "/home/claude/project/medtrip-connect-main/"
hdr = """// GENERATED from the client's supplied Word files (hospital_list_details.docx, IVF_doctors.docx) by scripts/import-nov9-content/.
// Wording and figures are as supplied (hyperlinks to Google searches removed, dashes as hyphens, a few typos listed in
// content-review/README.md corrected). Missing items are left empty on purpose - see content-review/README.md.
"""
# ---------- hospitals
pr = json.load(open("/tmp/claude-0/nov9/profiles.json"))
def split_pipes(items):
    out=[]
    for it in items:
        t=it["text"]
        if "|" in t and t.count("|")>=2:
            head=None
            if "\n" in t: head,t=t.split("\n",1)
            parts=[p.strip() for p in t.split("|") if p.strip()]
            if head: out.append({"text":head.strip(),"children":[{"text":p} for p in parts]})
            else: out.extend({"text":p} for p in parts)
        else:
            if "children" in it: it["children"]=split_pipes(it["children"])
            out.append(it)
    return out
for slug,p in pr.items():
    for bl in p["blocks"]:
        if bl["t"]=="list": bl["items"]=split_pipes(bl["items"])
    p["gallery"]=[{"src":g["src"],"w":g["w"],"h":g["h"]} for g in p["gallery"]]
    p.pop("docName",None)
open(P+"src/data/hospital-profiles.ts","w").write(hdr+'''import type { HospitalProfile } from "./content-types";

export const HOSPITAL_PROFILES: Record<string, HospitalProfile> = '''+json.dumps(pr,ensure_ascii=False,indent=1)+";\n")
# ---------- IVF doctors
b = json.load(open("/tmp/claude-0/nov9/ivf.json"))
idx=[i for i,x in enumerate(b) if x["t"]=="h" and re.match(r"(\d+\.\s*)?Dr\.? ",x["text"])]+[len(b)]
docs=[]
for a,z in zip(idx,idx[1:]):
    s=b[a:z]; name=re.sub(r"^\d+\.\s*","",s[0]["text"]).strip()
    img=next(x["file"] for x in s if x["t"]=="img")
    meta=next(x["text"] for x in s if x["t"]=="p" and "Designation" in x["text"])
    g=lambda k: re.search(r"\*\*"+k+r":\*\*\s*(.*)",meta).group(1).strip()
    sec=None; profile=[]; lists={}
    for x in s[1:]:
        if x["t"]=="h": sec=x["text"].strip(); lists.setdefault(sec,[]); continue
        if x["t"]=="p" and sec=="Professional Profile": profile.append(x["text"].strip())
        elif x["t"]=="li" and sec: lists[sec].append(x["text"].strip())
    slug="dr-"+re.sub(r"[^a-z0-9]+","-",re.sub(r"^Dr\.?\s*","",name).lower()).strip("-")
    os.makedirs(P+"public/doctors",exist_ok=True)
    im=Image.open("/tmp/claude-0/nov9/media_i/"+img).convert("RGB"); im.save(P+f"public/doctors/{slug}.webp","WEBP",quality=90,method=6)
    md="## Professional Profile\n\n"+"\n\n".join(profile)
    for k,v in lists.items():
        if v and k!="Professional Profile": md+=f"\n\n## {k}\n\n"+"\n".join("- "+i for i in v)
    docs.append(dict(slug=slug,name=name,designation=g("Designation"),qualifications=g("Qualifications"),location=g("Location"),summary=profile[0],body=md,image_url=f"/doctors/{slug}.webp",image_alt=name,imageW=im.size[0],imageH=im.size[1]))
dash=lambda t: re.sub(r"\s*[–—]\s*",lambda m:" - " if m.group(0).strip()!=m.group(0) else "-",t)
docs=json.loads(dash(json.dumps(docs,ensure_ascii=False)))
open(P+"src/data/nova-ivf-doctors.ts","w").write(hdr+'''
export type NovaIvfDoctor = { slug: string; name: string; designation: string; qualifications: string; location: string; summary: string; body: string; image_url: string; image_alt: string };
export const NOVA_IVF_HOSPITAL_SLUG = "nova-ivf-fertility";
export const NOVA_IVF_DOCTORS: NovaIvfDoctor[] = '''+json.dumps([{k:v for k,v in d.items() if k not in("imageW","imageH")} for d in docs],ensure_ascii=False,indent=1)+";\n")
print([d["slug"] for d in docs])
