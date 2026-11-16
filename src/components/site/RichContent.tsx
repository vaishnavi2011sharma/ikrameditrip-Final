import { Link } from "@tanstack/react-router";
import { Inline } from "@/components/site/cards";
import type { ContentBlock, ListItem } from "@/data/content-types";
import { COST_PAGES } from "@/data/cost-pages";

function Items({ items, ordered }: { items: ListItem[]; ordered: boolean }) {
  const Tag = ordered ? "ol" : "ul";
  return (
    <Tag
      className={`${ordered ? "list-decimal marker:font-semibold" : "list-disc"} space-y-2 pl-6 leading-relaxed marker:text-primary`}
    >
      {items.map((it, i) => (
        <li key={i}>
          {it.href ? (
            <a href={it.href} className="text-primary hover:underline">
              {it.text}
            </a>
          ) : (
            <Inline text={it.text} />
          )}
          {it.children?.length ? (
            <div className="mt-2">
              <Items items={it.children} ordered={false} />
            </div>
          ) : null}
        </li>
      ))}
    </Tag>
  );
}

/** Renders structured medical content (headings, text, cost lines, tables, lists, images) in the site's existing style. */
export function RichContent({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-4 text-muted-foreground">
      {blocks.map((b, i) => {
        switch (b.t) {
          case "h": {
            const cls =
              b.lvl === 2
                ? "pt-6 text-2xl font-semibold tracking-tight text-foreground"
                : "pt-3 text-xl font-semibold text-foreground";
            const inner = b.href ? (
              <a href={b.href} className="text-primary underline-offset-2 hover:underline">
                {b.text}
              </a>
            ) : (
              b.text
            );
            return b.lvl === 2 ? (
              <h2 key={i} className={cls}>
                {inner}
              </h2>
            ) : (
              <h3 key={i} className={cls}>
                {inner}
              </h3>
            );
          }
          case "p":
            return (
              <p key={i} className="leading-relaxed">
                <Inline text={b.text} />
              </p>
            );
          case "note":
            return (
              <p
                key={i}
                className="rounded-xl border border-border bg-muted/40 p-4 text-sm leading-relaxed"
              >
                <Inline text={b.text} />
              </p>
            );
          case "cost":
            return b.href ? (
              <a
                key={i}
                href={b.href}
                className="block rounded-xl border border-primary/30 bg-primary/5 p-4 font-semibold text-primary shadow-card hover:shadow-lift"
              >
                <Inline text={b.text} /> <span aria-hidden>→</span>
              </a>
            ) : (
              <p
                key={i}
                className="rounded-xl border border-primary/20 bg-primary/5 p-4 font-semibold text-foreground"
              >
                <Inline text={b.text} />
              </p>
            );
          case "facts":
            return (
              <dl
                key={i}
                className="grid gap-3 rounded-2xl border border-border bg-card p-5 shadow-card sm:grid-cols-2 lg:grid-cols-3"
              >
                {b.items.map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {k}
                    </dt>
                    <dd className="mt-1 font-semibold text-foreground">{v}</dd>
                  </div>
                ))}
              </dl>
            );
          case "list":
            return <Items key={i} items={b.items} ordered={b.ordered} />;
          case "table":
            return (
              <div key={i} className="overflow-x-auto rounded-xl border border-border">
                <table className="w-full min-w-[28rem] text-left text-sm">
                  {b.head ? (
                    <thead className="bg-muted/60 text-foreground">
                      <tr>
                        {b.head.map((c, k) => (
                          <th key={k} scope="col" className="px-4 py-3 font-semibold">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                  ) : null}
                  <tbody className="divide-y divide-border">
                    {b.rows.map((r, ri) => (
                      <tr key={ri}>
                        {r.map((c, k) =>
                          k === 0 ? (
                            <th
                              key={k}
                              scope="row"
                              className="whitespace-pre-line px-4 py-3 text-left font-medium text-foreground"
                            >
                              <Inline text={c} />
                            </th>
                          ) : (
                            <td key={k} className="whitespace-pre-line px-4 py-3">
                              <Inline text={c} />
                            </td>
                          ),
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          case "img":
            return (
              <figure key={i} className="overflow-hidden rounded-2xl border border-border bg-card">
                <img
                  src={b.src}
                  alt={b.alt}
                  width={b.w}
                  height={b.h}
                  loading="lazy"
                  decoding="async"
                  className="h-auto w-full object-contain"
                />
              </figure>
            );
        }
      })}
    </div>
  );
}

/** Clickable treatment-cost cards: each shows the supplied estimate line and opens its own detail page. */
export function CostGuideCards({
  deptSlug,
  title = "Treatment costs",
}: {
  deptSlug: string;
  title?: string;
}) {
  const pages = COST_PAGES.filter((p) => p.showOn.includes(deptSlug));
  if (!pages.length) return null;
  return (
    <section aria-labelledby="cost-guides" className="mx-auto max-w-6xl px-4 pb-10">
      <h2 id="cost-guides" className="text-2xl font-semibold tracking-tight text-foreground">
        {title}
      </h2>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        Select a treatment to open its detailed cost page. Figures are estimates and vary by
        hospital, doctor and condition.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {pages.map((p) => (
          <Link
            key={p.slug}
            to="/treatment-cost/$slug"
            params={{ slug: p.slug }}
            className="group rounded-2xl border border-border bg-card p-5 shadow-card hover:shadow-lift"
          >
            <h3 className="font-semibold text-foreground group-hover:text-primary">{p.name}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{p.listCost}</p>
            <span className="mt-3 inline-block text-sm font-semibold text-primary">
              View cost details →
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
