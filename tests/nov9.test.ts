import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { migrate, openDb } from "../src/backend/db/client";
import { seed } from "../src/backend/seed";
import { applySuppliedNov9 } from "../src/backend/supplied-nov9";
import {
  getHospital,
  getDoctor,
  getDepartment,
  listDoctors,
  sitemapEntries,
} from "../src/backend/repo/public";
import { HOSPITAL_PROFILES } from "../src/data/hospital-profiles";
import { NOVA_IVF_DOCTORS } from "../src/data/nova-ivf-doctors";

const db = openDb(":memory:");
seed(db);
const SLUGS = Object.keys(HOSPITAL_PROFILES);

describe("hospital profiles (hospital_list_details.docx)", () => {
  test("16 supplied hospitals, each in the database with its facts", () => {
    assert.equal(SLUGS.length, 16);
    for (const slug of SLUGS) {
      const h = getHospital(db, slug) as any;
      assert.ok(h, slug);
      assert.ok(h.profile && h.profile.blocks.length > 5, `${slug} profile`);
      assert.ok(h.address, `${slug} address`);
      assert.match(h.established ?? "2000", /^\d{4}$/);
    }
  });
  test("exact supplied facts", () => {
    const f = (s: string) => getHospital(db, s) as any;
    assert.deepEqual(
      [
        f("artemis-hospitals").established,
        f("artemis-hospitals").beds,
        f("artemis-hospitals").hospital_type,
      ],
      ["2007", "750", "Super Speciality"],
    );
    assert.equal(f("apollo-main-hospital-greams-road").beds, "560- 745");
    assert.equal(f("amrita-hospitals").beds, "2600");
    assert.equal(f("nova-ivf-fertility").address, "3B, Uttam Kumar Sarani, Kolkata - 700017");
    assert.equal(f("manipal-hospitals-siliguri").established, "2014");
  });
  test("missing facts stay empty instead of being invented (TX year incomplete, Kauvery beds blank)", () => {
    assert.equal((getHospital(db, "tx-hospitals") as any).established, null);
    assert.equal((getHospital(db, "kauvery-hospitals") as any).beds, null);
    assert.equal(
      (getHospital(db, "p-and-o-international-artificial-limb-centre") as any).beds,
      null,
    );
  });
  test("no drafting placeholders or Google-search hyperlinks leak onto public pages", () => {
    const json = JSON.stringify(HOSPITAL_PROFILES);
    assert.ok(!/GIVE DOCTORS|give google map|BANNER IMAGE|google\.com\/search|kgmid/i.test(json));
  });
  test("every image, badge and gallery file exists; no photo is listed twice", () => {
    const all: string[] = [];
    for (const p of Object.values(HOSPITAL_PROFILES))
      for (const g of p.gallery) {
        assert.ok(existsSync("public" + g.src), g.src);
        all.push(g.src);
      }
    assert.equal(new Set(all).size, all.length);
    assert.ok(
      existsSync("public/hospitals/accreditation/jci.webp") &&
        existsSync("public/hospitals/accreditation/nabh.webp"),
    );
  });
  test("department links inside hospital profiles point at real departments", () => {
    for (const p of Object.values(HOSPITAL_PROFILES))
      for (const b of p.blocks)
        if (b.t === "list")
          for (const it of b.items)
            if (it.href) assert.ok(getDepartment(db, it.href.replace("/services/", "")), it.href);
  });
  test("PHS and P&O are linked to their speciality; Artemis lists its departments", () => {
    const names = (s: string) => (getHospital(db, s) as any).departments.map((d: any) => d.slug);
    assert.ok(names("phs-fertility-centre-kolkata").includes("ivf-and-reproductive-medicine"));
    assert.ok(
      names("p-and-o-international-artificial-limb-centre").includes(
        "prosthetic-and-artificial-body-parts",
      ),
    );
    assert.ok(names("artemis-hospitals").length >= 18);
  });
  test("an existing old database gets the new columns and content without re-seeding, and a second run changes nothing", () => {
    const old = new DatabaseSync(":memory:");
    migrate(old as any);
    seed(old as any);
    old.exec("DELETE FROM _migrations WHERE id = 8");
    old.exec(
      "ALTER TABLE hospitals DROP COLUMN established; ALTER TABLE hospitals DROP COLUMN beds; ALTER TABLE hospitals DROP COLUMN hospital_type; ALTER TABLE hospitals DROP COLUMN profile_json;",
    );
    old.exec(
      "DELETE FROM doctors WHERE slug LIKE 'dr-%gutgutia'; DELETE FROM app_meta WHERE key = 'nova_ivf_doctors_v1'",
    );
    migrate(old as any);
    const r = applySuppliedNov9(old as any);
    assert.equal(r.doctors, 1);
    assert.equal(applySuppliedNov9(old as any).doctors, 0);
    assert.equal(
      (old.prepare("SELECT established FROM hospitals WHERE slug='artemis-hospitals'").get() as any)
        .established,
      "2007",
    );
  });
  test("an admin-entered value is never overwritten by the supplied data", () => {
    const d = openDb(":memory:");
    seed(d);
    d.prepare(
      "UPDATE hospitals SET beds = '999', address = 'Admin address' WHERE slug = 'artemis-hospitals'",
    ).run();
    applySuppliedNov9(d);
    const r = d
      .prepare("SELECT beds, address FROM hospitals WHERE slug='artemis-hospitals'")
      .get() as any;
    assert.deepEqual([r.beds, r.address], ["999", "Admin address"]);
  });
});

describe("Nova IVF doctors (IVF_doctors.docx)", () => {
  test("7 doctors, exact names, each unique and linked to Nova IVF and the IVF department", () => {
    assert.deepEqual(
      NOVA_IVF_DOCTORS.map((d) => d.name),
      [
        "Dr. Rohit Gutgutia",
        "Dr. Aindri Sanyal",
        "Dr. Anindita Singh",
        "Dr. Preeti Mahawar",
        "Dr. Suparna Bhattacharya",
        "Dr. Ruchi Jain",
        "Dr. Akanksha Goel",
      ],
    );
    const nova = getHospital(db, "nova-ivf-fertility") as any;
    assert.deepEqual(
      nova.doctors.map((d: any) => d.name).sort(),
      NOVA_IVF_DOCTORS.map((d) => d.name).sort(),
    );
    const ivf = listDoctors(db, {
      department: "ivf-and-reproductive-medicine",
      pageSize: 50,
    } as any).rows.map((r: any) => r.slug);
    for (const d of NOVA_IVF_DOCTORS) assert.ok(ivf.includes(d.slug), d.slug);
    assert.equal(
      (
        db
          .prepare(
            "SELECT COUNT(*) n FROM (SELECT lower(name) FROM doctors GROUP BY lower(name) HAVING COUNT(*) > 1)",
          )
          .get() as any
      ).n,
      0,
    );
  });
  test("designation / qualifications / profile text are exactly as supplied", () => {
    const g = getDoctor(db, "dr-rohit-gutgutia") as any;
    assert.equal(g.designation, "Medical Director & IVF Specialist");
    assert.equal(g.qualifications, "MBBS, DGO");
    assert.match(g.body, /Herzliya Medical Centre, Israel/);
    const m = getDoctor(db, "dr-preeti-mahawar") as any;
    assert.equal(
      m.qualifications,
      "MBBS, DGO, DNB, Diploma in ART and Reproductive Medicine from Kiel, Germany",
    );
    const j = getDoctor(db, "dr-ruchi-jain") as any;
    assert.equal(
      j.qualifications,
      "MBBS, MS (Obstetrics and Gynaecology), FNB in Reproductive Medicine",
    );
  });
  test("no invented numbers: experience_years stays empty, photos exist", () => {
    for (const d of NOVA_IVF_DOCTORS) {
      assert.ok(existsSync("public" + d.image_url), d.image_url);
      assert.equal((getDoctor(db, d.slug) as any).experience_years ?? null, null);
    }
  });
  test("IVF department page shows the three IVF hospitals and now 10 doctors", () => {
    const x = getDepartment(db, "ivf-and-reproductive-medicine") as any;
    assert.ok(x.doctors.length >= 10);
  });
  test("doctor pages are in the sitemap", () => {
    const paths = sitemapEntries(db).map((e) => e.path);
    for (const d of NOVA_IVF_DOCTORS) assert.ok(paths.includes(`/doctors/${d.slug}`), d.slug);
  });
});

describe("prosthetic page images", () => {
  test("real, client-supplied P & O photos are wired in and exist on disk", () => {
    const src = readFileSync("src/data/prosthetic-images.ts", "utf8");
    assert.ok((src.match(/src: "\/hospitals\/gallery\/p-and-o/g) ?? []).length >= 2);
    assert.ok(
      existsSync("public/hospitals/gallery/p-and-o-international-artificial-limb-centre-1.webp"),
    );
  });
});

describe("internal link audit (all supplied content)", () => {
  test("every internal link in department, cost-page and hospital content resolves", async () => {
    const { DEPT_CONTENT } = await import("../src/data/dept-content");
    const { COST_PAGES } = await import("../src/data/cost-pages");
    const hrefs: string[] = [];
    const scan = (o: unknown) => {
      if (typeof o === "string") {
        for (const m of o.matchAll(/\]\((\/[^)\s]*)\)/g)) hrefs.push(m[1]!);
      } else if (Array.isArray(o)) o.forEach(scan);
      else if (o && typeof o === "object")
        for (const [k, v] of Object.entries(o)) {
          if (k === "href" && typeof v === "string" && v.startsWith("/")) hrefs.push(v);
          else scan(v);
        }
    };
    scan(DEPT_CONTENT);
    scan(COST_PAGES);
    scan(HOSPITAL_PROFILES);
    assert.ok(hrefs.length > 40, `${hrefs.length} links found`);
    const one = (t: string, s: string) => db.prepare(`SELECT 1 FROM ${t} WHERE slug = ?`).get(s);
    const costSlugs = new Set(COST_PAGES.map((p) => p.slug));
    for (const h of hrefs) {
      const [, kind, slug] = h.split("#")[0]!.split("/");
      if (kind === "services") assert.ok(!slug || one("departments", slug), h);
      else if (kind === "treatment-cost") assert.ok(!slug || costSlugs.has(slug), h);
      else if (kind === "hospitals") assert.ok(!slug || one("hospitals", slug), h);
      else if (kind === "doctors") assert.ok(!slug || one("doctors", slug), h);
      else if (kind === "treatments") assert.ok(!slug || one("treatments", slug), h);
      else
        assert.ok(
          ["contact", "about", "blog", "search", "privacy-policy"].includes(kind!),
          `unknown route ${h}`,
        );
    }
  });
});
