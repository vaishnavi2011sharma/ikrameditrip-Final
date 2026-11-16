/**
 * Real, licensed photographs for the Prosthetic / Artificial Body Parts department page.
 * Raunak's department document has none; the only real prosthetics photos supplied are the two P & O International centre photos from the hospital list document (shop front and entrance). No product / limb photos exist yet and none have been invented. To publish them:
 * put the files in public/content/prosthetics/ and add an entry here with honest alt text
 * (and the licence / credit, which is shown as the caption). The gallery appears automatically.
 */
export type ProstheticImage = {
  src: string;
  alt: string;
  width: number;
  height: number;
  credit: string;
};
export const PROSTHETIC_IMAGES: ProstheticImage[] = [
  {
    src: "/hospitals/gallery/p-and-o-international-artificial-limb-centre-1.webp",
    alt: "P & O International artificial limb centre, Lajpat Nagar, New Delhi - shop front",
    width: 1200,
    height: 897,
    credit: "P & O International, New Delhi (photo supplied by the client)",
  },
  {
    src: "/hospitals/gallery/p-and-o-international-artificial-limb-centre-2.webp",
    alt: "P & O International artificial limb centre, Lajpat Nagar, New Delhi - entrance",
    width: 703,
    height: 1054,
    credit: "P & O International, New Delhi (photo supplied by the client)",
  },
];
