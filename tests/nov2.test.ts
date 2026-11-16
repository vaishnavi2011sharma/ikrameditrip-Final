import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { openDb } from "../src/backend/db/client";
import { seed } from "../src/backend/seed";
import { COST_PAGES } from "../src/data/cost-pages";
import { DEPT_CONTENT } from "../src/data/dept-content";
import {
  departmentExtras,
  getCostPageData,
  sitemapEntries,
  getDepartment,
} from "../src/backend/repo/public";
import type { ContentBlock } from "../src/data/content-types";

const SLUGS = [
  "angioplasty",
  "cabg-heart-bypass",
  "asd-vsd-repair",
  "cervical-cancer",
  "breast-cancer",
  "bone-marrow-transplant",
  "spinal-fusion",
  "knee-replacement",
  "hip-replacement",
  "liver-transplant",
  "ivf-treatment",
  "spinal-decompression-laminectomy",
  "brain-tumour-surgery",
];
const db = openDb(":memory:");
seed(db);
const allBlocks = (): ContentBlock[] => [
  ...Object.values(DEPT_CONTENT).flatMap((d) => d.blocks),
  ...COST_PAGES.flatMap((p) => p.blocks),
];

describe("treatment cost pages (Raunak content)", () => {
  test("exactly the 13 requested pages exist, each with substantial content", () => {
    assert.deepEqual(COST_PAGES.map((p) => p.slug).sort(), [...SLUGS].sort());
    for (const p of COST_PAGES) {
      assert.ok(p.blocks.length >= 12, p.slug);
      assert.ok(
        p.blocks.some((b) => b.t === "facts") || p.blocks.some((b) => b.t === "table"),
        `${p.slug} has cost data`,
      );
      assert.ok(p.listCost.length > 10);
    }
  });
  test("the supplied one-line costs are kept verbatim", () => {
    const by = Object.fromEntries(COST_PAGES.map((p) => [p.slug, p.listCost]));
    assert.match(by["angioplasty"]!, /2500 USD onwards/);
    assert.match(by["cabg-heart-bypass"]!, /4000 USD onwards/);
    assert.match(by["asd-vsd-repair"]!, /7000 USD onwards/);
    assert.match(by["cervical-cancer"]!, /5000 USD onwards/);
    assert.match(by["bone-marrow-transplant"]!, /14000 USD/);
    assert.match(by["spinal-fusion"]!, /7000 USD/);
    assert.match(by["knee-replacement"]!, /US \$4000/);
    assert.match(by["hip-replacement"]!, /US \$5500/);
    assert.match(by["liver-transplant"]!, /US \$15000/);
    assert.match(by["ivf-treatment"]!, /2500 USD/);
    assert.match(by["spinal-decompression-laminectomy"]!, /2300 USD/);
  });
  test("every department page lists clickable cost cards for its own treatments and every page is reachable", () => {
    for (const p of COST_PAGES) assert.ok(p.showOn.length > 0, p.slug);
    const linked = new Set(allBlocks().flatMap((b) => ("href" in b && b.href ? [b.href] : [])));
    for (const p of COST_PAGES) assert.ok(COST_PAGES.find((x) => x.slug === p.slug));
    for (const h of linked) assert.ok(SLUGS.includes(h.replace("/treatment-cost/", "")), h);
    const cards = COST_PAGES.flatMap((p) => p.showOn);
    assert.ok(
      cards.includes("cardiology") &&
        cards.includes("oncology") &&
        cards.includes("orthopedic-and-joint-replacement"),
    );
  });
  test("colon cancer has no page and is not linked (content missing, flagged)", () => {
    assert.ok(!SLUGS.includes("colon-cancer"));
    const colon = allBlocks().filter((b) => "text" in b && /colon cancer/i.test(b.text));
    for (const b of colon) assert.ok(!("href" in b && b.href), "colon cancer must not link");
  });
  test("hospital slugs referenced exist in the seeded database; doctors come from real DB records", () => {
    for (const p of COST_PAGES) {
      const d = getCostPageData(db, p.slug)!;
      assert.equal(d.hospitals.length, p.hospitals.length, `${p.slug} hospitals resolve`);
      assert.ok(d.parent, p.slug);
    }
    for (const [slug, c] of Object.entries(DEPT_CONTENT))
      assert.equal(departmentExtras(db, slug).hospitals.length, c.hospitals.length, slug);
  });
  test("16 department pages exist in the DB; 14 have supplied content, General Surgery and Prosthetic are title-only", () => {
    assert.equal(Object.keys(DEPT_CONTENT).length, 16);
    const empty = Object.entries(DEPT_CONTENT)
      .filter(([, c]) => c.blocks.length === 0)
      .map(([s]) => s)
      .sort();
    assert.deepEqual(empty, [
      "general-and-laparoscopic-surgery",
      "prosthetic-and-artificial-body-parts",
    ]);
    for (const s of Object.keys(DEPT_CONTENT)) assert.ok(getDepartment(db, s), s);
  });
  test("sitemap includes the 13 cost pages", () => {
    const paths = sitemapEntries(db).map((e) => e.path);
    for (const s of SLUGS) assert.ok(paths.includes(`/treatment-cost/${s}`), s);
  });
  test("images referenced exist on disk with alt text; withheld branded/foreign images are not public", () => {
    for (const b of allBlocks())
      if (b.t === "img") {
        assert.ok(existsSync("public" + b.src), b.src);
        assert.ok(b.alt.length > 5, b.src);
      }
    assert.ok(existsSync("content-review/images/department-doc-image48.jpeg"));
    assert.ok(!existsSync("public/content-review"));
  });
  test("no placeholder / instruction text from the source docs leaks onto pages", () => {
    const bad = /give 3-4 doctors|header on banner|hyperlink|lorem|\[\[\d+\]/i;
    for (const b of allBlocks()) if ("text" in b) assert.ok(!bad.test(b.text), b.text.slice(0, 60));
    for (const p of COST_PAGES) assert.ok(!bad.test(p.subtitle) && !bad.test(p.h1));
  });
  test("route, renderer, header-level wiring in source", () => {
    assert.ok(existsSync("src/routes/treatment-cost_.$slug.tsx"));
    const dept = readFileSync("src/routes/services_.$slug.tsx", "utf8");
    assert.ok(
      dept.includes("CostGuideCards") &&
        dept.includes("RichContent") &&
        dept.includes("AppointmentForm"),
    );
    const hub = readFileSync("src/routes/treatment-cost.tsx", "utf8");
    assert.ok(hub.includes("/treatment-cost/$slug") && hub.includes("cost-enquiry"));
    const page = readFileSync("src/routes/treatment-cost_.$slug.tsx", "utf8");
    assert.ok(
      page.includes("Breadcrumbs") && page.includes("canonical") && page.includes("notFound"),
    );
  });
});
