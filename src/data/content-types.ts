export type ContentBlock =
  | { t: "h"; text: string; lvl: 2 | 3; href?: string }
  | { t: "p"; text: string }
  | { t: "note"; text: string }
  | { t: "cost"; text: string; href?: string }
  | { t: "facts"; items: [string, string][] }
  | { t: "list"; ordered: boolean; items: ListItem[] }
  | { t: "table"; head: string[] | null; rows: string[][] }
  | { t: "img"; src: string; alt: string; w: number; h: number };
export interface ListItem {
  text: string;
  href?: string;
  children?: ListItem[];
}

export interface DeptContent {
  docTitle: string;
  blocks: ContentBlock[];
  hospitals: string[];
  hospitalsListed: string[];
  hospitalsHeading: string | null;
  doctorsNote: string | null;
}
export interface CostPage {
  slug: string;
  name: string;
  h1: string;
  subtitle: string;
  parent: string;
  doctorDepartments: string[];
  showOn: string[];
  listCost: string;
  blocks: ContentBlock[];
  hospitals: string[];
  hospitalsListed: string[];
  hospitalsHeading: string | null;
  doctorsHeading: string | null;
}

export interface HospitalProfile {
  established: string | null;
  beds: string | null;
  type: string | null;
  /** city exactly as written in the supplied document (the database city is what the site uses) */
  docLocation: string | null;
  address: string | null;
  accreditation: ("JCI" | "NABH")[];
  blocks: ContentBlock[];
  gallery: { src: string; w: number; h: number }[];
}
