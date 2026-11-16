# Content review - items for Raunak's confirmation

Source: `treatment.docx` (16 department pages) and `treatment_SUB_PAGES.docx` (13 cost pages). Text is imported
programmatically (`scripts/import-raunak-content/`), wording and figures unchanged. Only typography was normalised
(en/em dashes to plain hyphens, per the site-wide rule) and 4 obvious copy errors fixed (listed below).

## 1. Missing content (not invented)
- **Colon Cancer**: in the cost list and department text (6000 USD) but no detailed content supplied. No page created; shown as plain, unlinked text.
- **General & Laparoscopic Surgery** and **Prosthetic & Artificial Body Parts**: the document has the title only. Pages show existing site data (hospitals, doctors, enquiry form) only.
- **Prosthetic page images (compulsory)**: the document contains none and none could be sourced or licensed from this environment (no external image access). Drop real files into `public/content/prosthetics/` and add entries (with credit) to `src/data/prosthetic-images.ts`; the gallery appears automatically.
- Banner/header images for cost pages were not supplied.
- IVF hospital list names Zemya twice and the third entry is missing; the neurology list heading is garbled ("TOP HOSPITALS FOR TOP HOSPITALS FOR...").
- Our site also has Neurosurgery, Haemato-Oncology and Cardio-Thoracic departments with no own content; they show the relevant cost cards only.

## 2. Conflicting figures (kept exactly as supplied - please confirm which is correct)
| Treatment | One-line list figure | Elsewhere in supplied content |
|---|---|---|
| Angioplasty | 2500 USD onwards | dept table $3,000-$4,000 (1 stent); page min 2500 / max 5000 |
| CABG | 4000 USD onwards | dept table $4,500-$7,500; page 4000-8000; intro "$2,000-$7,000" |
| ASD/VSD | 7000 USD onwards | page: ASD 2500-5000, VSD 4000-7500 |
| Cervical cancer | 5000 USD onwards | page intro "starts from 3000"; min 3000 / max 6500; dept table 4,000-6,000 |
| Breast cancer | 5500 USD onwards | page min 2500 / max 7500; dept table 4,000-6,000 |
| Bone marrow transplant | from 14000 USD | page min 16000 / max 40000; autologous table $16,000-$22,000 |
| Spinal fusion | 7000 USD | page min 4500 / max 8000; lumbar table 5,500-10,000 |
| Knee replacement | from US $4000 | page min 3500 / max 10000; table 3,500-7,500 |
| Hip replacement | from US $5500 | page min 4500 / max 8000; table 4500-6500 |
| Liver transplant | from US $15000 | page min 15000 / max 25000 |
| IVF | from 2500 USD | page min 2500 / max 5000 |
| Laminectomy | 2300 USD | page min 3800 / max 5400; ortho dept says 4000 (laminotomy), table 4,000-8,000 |
| Brain tumour | oncology 6500 / neurology 5000 | page min 4500 / max 9000 |

Mislabelled cost lines in the orthopaedic section (revision / shoulder / foot lines saying "knee replacement", "meniscus repair 2500 USD ... starts US $4000", repeated vertebroplasty 5000/4000) and the cardiology "valve" vs "arrhythmia" 5500/3500 lines are also kept as supplied.

## 3. Copy errors corrected (only these)
- ['cabg-heart-bypass', 'heading', 'FACTORS THAT AFFECT THE ANGIOPLASTY COST IN INDIA', 'FACTORS THAT AFFECT THE CABG COST IN INDIA']
- ['asd-vsd-repair', 'banner subtitle', 'cost of bypass surgery in India', 'cost of ASD/VSD repair surgery in India']
- ['breast-cancer', 'banner subtitle', 'cost of colon cancer treatment in India', 'cost of breast cancer treatment in India']
- ['liver-transplant', 'banner subtitle', 'cost of bypass surgery in India', 'cost of liver transplant in India']
Also noted, left as supplied: typos "OPTHALMOLOGY", "PULMUNOLOGY", "TRANSPPLANT"; eye-doctor note says "CARDIOLOGY DEPARTMENT"; Dentistry "Oral cancer surgery" text duplicates the jaw-correction text.

## 4. Hospital naming to verify
"Apollo Indraprastha Hospital, Kolkata" (Indraprastha is in Delhi); "Kauvery Hospital, Kolkata" (our record is Bangalore); "Apollo Hospitals, Chennai" mapped to Apollo Main Hospital (Greams Road). Hospitals are shown from our own records.

## 5. Rights and licensing
Provenance of the supplied images is unverified. The Cosmetic Surgery text looks copied from Wikipedia (citation marks removed) - please verify licence/attribution. 48 of 66 images are published; **18 are withheld** (foreign-language captions, third-party branding/watermarks, redactions) and kept here in `content-review/images/` (not served publicly):

| File | Department | Reason |
|---|---|---|
| department-doc-image8.jpeg | orthopedic-and-joint-replacement | German caption ('Meniskusnaht') |
| department-doc-image11.jpeg | orthopedic-and-joint-replacement | Turkish caption ('Civi Ile Kirik Tespiti') |
| department-doc-image12.jpeg | orthopedic-and-joint-replacement | 'MEDICAL' vendor watermark |
| department-doc-image13.jpeg | orthopedic-and-joint-replacement | redacted patient/case label in the image |
| department-doc-image21.jpeg | orthopedic-and-joint-replacement | French caption ('Resultat de chirurgie scoliose') |
| department-doc-image28.jpeg | liver-transplant-gi-and-hpb-surgery | Cleveland Clinic copyright mark |
| department-doc-image29.jpeg | liver-transplant-gi-and-hpb-surgery | third-party logo mark |
| department-doc-image32.jpeg | liver-transplant-gi-and-hpb-surgery | Medicover Hospitals branding |
| department-doc-image37.jpeg | liver-transplant-gi-and-hpb-surgery | Mayo Foundation copyright mark |
| department-doc-image48.jpeg | neurology | Mayo Clinic copyright mark |
| department-doc-image51.jpeg | neurology | Healthline branding |
| department-doc-image53.jpeg | neurology | Mayo Foundation copyright mark |
| department-doc-image57.jpeg | neurology | Medicover Hospitals branding |
| department-doc-image58.jpeg | neurology | Mayo Foundation copyright mark |
| department-doc-image59.jpeg | neurology | Elekta product branding |
| department-doc-image60.jpeg | neurology | CyberKnife / Accuray product branding |
| department-doc-image62.jpeg | neurology | small copyright mark (unreadable) |
| department-doc-image65.jpeg | neurology | Mayo Foundation copyright mark |

To publish a withheld image, replace it with a licensed/own version and add it to the relevant block in `src/data/dept-content.ts`.

---

# Nov 9 update - hospital list and Nova IVF doctors

Sources: `hospital_list_details.docx` (16 hospitals), `IVF_doctors.docx` (7 doctors). Data: `src/data/hospital-profiles.ts`, `src/data/nova-ivf-doctors.ts`; loaded into the database by `src/backend/supplied-nov9.ts` (migration 8 adds `established`, `beds`, `hospital_type`, `profile_json`). Only EMPTY fields are filled, so admin edits are never overwritten.

## Missing or incomplete in the supplied hospital document (left empty, not invented)
- **Doctors for every hospital**: each section says "GIVE DOCTORS PROFILES" with nothing supplied. The site lists the doctors already linked in the database. Hospitals with NO linked doctors: Amrita, Apollo Main (Greams Road), Apollo Cancer Centre, Apollo Fertility Centre, Apollo Gleneagles, Fortis Escorts Hospital, Manipal Bangalore, Manipal Electronic City.
- **Google map location**: every section says "(give google map location)". No map is shown.
- **Banner image** placeholder text in the first two sections; existing hero photos were kept.
- **Established year**: TX Hospitals says "20" (incomplete) - left empty. **Beds**: Kauvery blank, P&O none - left empty. Apollo Main says "560- 745" - shown as supplied.
- **Address**: not supplied for the 6 hospitals that are not in the document (Apollo Cancer Centre, Apollo Fertility Centre, Apollo Gleneagles, Fortis Escorts Hospital, Manipal Bangalore, Manipal Electronic City).
- **Fortis Hospital Kolkata** has no linked speciality (its document lists services, not department names).
- Zemya IVF has an "Awards and recognition" heading with nothing under it - heading removed.
- **Manipal**: the document has ONE Manipal entry (Siliguri). The site also holds two Bangalore Manipal entries from an earlier list; they are kept (not deleted) but have no supplied profile.

## Details to confirm
- Location vs address: AIMS and Amrita are labelled "Delhi" but their addresses are in Faridabad (the site shows the address as supplied; the database city stays Faridabad).
- **Accreditation badges** (JCI / NABH logos) are shown exactly where the document places them (Artemis, Apollo Main, Apollo Indraprastha: both; PHS, Desun, TX: both; Nova, AIMS, Amrita, Fortis x2, Kauvery, Manipal, Sharp Sight: NABH). Zemya and P&O show none. Please confirm each is correct - accreditation is a factual claim.
- The TX text "the hospital's services can be presented around the following treatment journey, subject to confirmation of the current international pat..." reads like a drafting note; kept as supplied.
- Typo "Opthamology" in treatment lists shown as "Ophthalmology" (only change to wording).
- Google-search hyperlinks inside award names (Apollo Main) were removed; the text is unchanged.
- IVF doctor experience statements ("more than 24 years", "more than 20 years") are kept only inside the profile text; the numeric experience field is left empty.
- Dr Aindri Sanyal profile text says "more than 11 years" as an IVF specialist "according to her official Nova profile".

## Images (hospitals)
100 images in the document: 65 published as gallery photos (`public/hospitals/gallery/`), 21 accreditation logos (shown as badges), 2 Google Maps screenshots and 11 very small images (under 400 px wide, would look blurred) and 1 unlabelled personal portrait (P&O) NOT used. Provenance and licensing of all supplied photos is unverified (several carry web-page titles as alt text, i.e. were likely copied from the hospitals' websites) - please confirm Ikra Meditrip may use them. The 7 doctor photos are 180x200 px, so they look soft on large screens.
Prosthetic department page: the two real P & O International photos (shop front, entrance) are now shown. There are still NO photos of prostheses/artificial limbs, so the "compulsory relevant images" requirement is only partly met.
