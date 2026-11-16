import type { DB } from "./db/client";
import { HOSPITAL_PROFILES } from "../data/hospital-profiles";
import { NOVA_IVF_DOCTORS, NOVA_IVF_HOSPITAL_SLUG } from "../data/nova-ivf-doctors";

/**
 * Client-supplied hospital profiles (hospital_list_details.docx). Fills only EMPTY columns, so anything an admin typed is kept.
 * profile_json holds the structured sections (about/services/awards), the photo gallery and the accreditation badges.
 */
export function applyHospitalProfiles(db: DB): number {
  const upd = db.prepare(
    `UPDATE hospitals SET
       established   = COALESCE(NULLIF(established, ''), ?),
       beds          = COALESCE(NULLIF(beds, ''), ?),
       hospital_type = COALESCE(NULLIF(hospital_type, ''), ?),
       address       = COALESCE(NULLIF(address, ''), ?),
       profile_json  = COALESCE(NULLIF(profile_json, ''), ?)
     WHERE slug = ?`,
  );
  const link = db.prepare(
    `INSERT OR IGNORE INTO hospital_departments (hospital_id, department_id)
     SELECT h.id, d.id FROM hospitals h, departments d WHERE h.slug = ? AND d.slug = ?`,
  );
  // a fertility centre / a prosthetics centre: the supplied documents describe nothing else, so the speciality link is certain
  const SPECIALITY: Record<string, string> = {
    "phs-fertility-centre-kolkata": "ivf-and-reproductive-medicine",
    "p-and-o-international-artificial-limb-centre": "prosthetic-and-artificial-body-parts",
  };
  let n = 0;
  for (const [slug, p] of Object.entries(HOSPITAL_PROFILES)) {
    const profile = JSON.stringify({
      blocks: p.blocks,
      gallery: p.gallery,
      accreditation: p.accreditation,
    });
    const first = db
      .prepare(
        "SELECT 1 FROM hospitals WHERE slug = ? AND (profile_json IS NULL OR profile_json = '')",
      )
      .get(slug);
    n += Number(upd.run(p.established, p.beds, p.type, p.address, profile, slug).changes);
    // the hospital's own "Treatments offered" list names departments: link them (never removes anything)
    // (first load only, so a later admin change to a hospital's specialities is not undone on restart)
    if (!first) continue;
    for (const b of p.blocks)
      if (b.t === "list")
        for (const it of b.items) if (it.href) link.run(slug, it.href.replace("/services/", ""));
    if (SPECIALITY[slug]) link.run(slug, SPECIALITY[slug]);
  }
  return n;
}

const norm = (n: string) =>
  n
    .toLowerCase()
    .replace(/\b(dr|prof)\b\.?/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

/** Adds the 7 Nova IVF doctors (IVF_doctors.docx) once: no duplicates (matched by slug or normalised name), linked to Nova IVF + IVF department. */
export function applyNovaIvfDoctors(db: DB): number {
  const hosp = db.prepare("SELECT id FROM hospitals WHERE slug = ?").get(NOVA_IVF_HOSPITAL_SLUG) as
    | { id: number }
    | undefined;
  const dept = db
    .prepare("SELECT id FROM departments WHERE slug = 'ivf-and-reproductive-medicine'")
    .get() as { id: number } | undefined;
  if (!hosp || !dept) return 0;
  // one-time load: a doctor an admin later deletes or edits is not re-created on restart
  if (db.prepare("SELECT 1 FROM app_meta WHERE key = 'nova_ivf_doctors_v1'").get()) return 0;
  const existing = db.prepare("SELECT id, slug, name FROM doctors").all() as {
    id: number;
    slug: string;
    name: string;
  }[];
  const ins = db.prepare(
    `INSERT INTO doctors (slug, name, designation, qualifications, summary, body, image_url, image_alt, published, featured)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)`,
  );
  let added = 0;
  for (const d of NOVA_IVF_DOCTORS) {
    let id = existing.find((e) => e.slug === d.slug || norm(e.name) === norm(d.name))?.id;
    if (!id) {
      id = Number(
        ins.run(
          d.slug,
          d.name,
          d.designation,
          d.qualifications,
          d.summary,
          d.body,
          d.image_url,
          d.image_alt,
        ).lastInsertRowid,
      );
      added++;
    }
    db.prepare(
      "INSERT OR IGNORE INTO doctor_hospitals (doctor_id, hospital_id, is_primary) VALUES (?, ?, 1)",
    ).run(id, hosp.id);
    db.prepare(
      "INSERT OR IGNORE INTO doctor_departments (doctor_id, department_id) VALUES (?, ?)",
    ).run(id, dept.id);
  }
  db.prepare("INSERT OR IGNORE INTO app_meta (key, value) VALUES ('nova_ivf_doctors_v1', ?)").run(
    String(NOVA_IVF_DOCTORS.length),
  );
  return added;
}

export function applySuppliedNov9(db: DB) {
  return { hospitals: applyHospitalProfiles(db), doctors: applyNovaIvfDoctors(db) };
}
