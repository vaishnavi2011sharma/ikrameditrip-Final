import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { AppointmentForm } from "@/components/site/AppointmentForm";
import { Breadcrumbs, DoctorCard, HospitalPhoto } from "@/components/site/cards";
import { RichContent } from "@/components/site/RichContent";
import { COST_PAGES, costPageBySlug } from "@/data/cost-pages";
import { getCostPageData } from "@/lib/data-fns";
import { canonical, jsonLdScript } from "@/lib/search";

const strip = (t: string) => t.replace(/\*\*|\[([^\]]+)\]\([^)]*\)/g, "$1");

export const Route = createFileRoute("/treatment-cost_/$slug")({
  loader: async ({ params }) => {
    const page = costPageBySlug(params.slug);
    if (!page) throw notFound();
    const data = await getCostPageData({ data: { slug: params.slug } });
    if (!data) throw notFound();
    return { slug: params.slug, data };
  },
  head: ({ loaderData }) => {
    const page = loaderData ? costPageBySlug(loaderData.slug) : undefined;
    if (!page) return {};
    const lead = page.blocks.find((b) => b.t === "p");
    const desc = strip(lead && lead.t === "p" ? lead.text : page.subtitle || page.listCost).slice(
      0,
      200,
    );
    const title = `${page.name} Cost in India | Ikra Meditrip`;
    const url = canonical(`/treatment-cost/${page.slug}`);
    return {
      meta: [
        { title },
        { name: "description", content: desc },
        { property: "og:title", content: title },
        { property: "og:description", content: desc },
      ],
      links: [{ rel: "canonical", href: url }],
      scripts: [
        jsonLdScript({
          "@context": "https://schema.org",
          "@type": "MedicalWebPage",
          name: page.h1,
          url,
          description: desc,
          breadcrumb: {
            "@type": "BreadcrumbList",
            itemListElement: [
              { "@type": "ListItem", position: 1, name: "Home", item: canonical("/") },
              {
                "@type": "ListItem",
                position: 2,
                name: "Treatment cost",
                item: canonical("/treatment-cost"),
              },
              { "@type": "ListItem", position: 3, name: page.name, item: url },
            ],
          },
        }),
      ],
    };
  },
  component: CostPage,
});

function CostPage() {
  const { slug, data } = Route.useLoaderData();
  const page = costPageBySlug(slug)!;
  const others = COST_PAGES.filter((p) => p.slug !== slug && p.parent === page.parent);
  return (
    <>
      <Breadcrumbs
        items={[{ label: "Treatment cost", to: "/treatment-cost" }, { label: page.name }]}
      />
      <section className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          {page.h1}
        </h1>
        {page.subtitle ? (
          <p className="mt-3 max-w-3xl text-lg text-muted-foreground">{page.subtitle}</p>
        ) : null}
        <p className="mt-4 rounded-xl border border-primary/30 bg-primary/5 p-4 font-semibold text-foreground max-w-3xl">
          {page.listCost}
        </p>
        <div className="mt-6 max-w-4xl">
          <RichContent blocks={page.blocks} />
        </div>
        {data.parent ? (
          <p className="mt-8 text-sm">
            <Link
              to="/services/$slug"
              params={{ slug: data.parent.slug }}
              className="font-semibold text-primary hover:underline"
            >
              ← Back to {data.parent.name}
            </Link>
          </p>
        ) : null}
      </section>

      {data.hospitals.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {page.hospitalsHeading ?? `Best hospitals for ${page.name}`}
          </h2>
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {data.hospitals.map((h) => (
              <Link
                key={h.slug}
                to="/hospitals/$slug"
                params={{ slug: h.slug }}
                className="overflow-hidden rounded-2xl border border-border bg-card shadow-card hover:shadow-lift"
              >
                <HospitalPhoto
                  h={{ ...h, is_placeholder_image: h.image_url ? 0 : 1 }}
                  className="h-36 w-full"
                />
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-foreground">{h.name}</h3>
                  <p className="text-xs text-muted-foreground">
                    {h.city}, {h.country}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {data.doctors.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            Doctors for {page.name}
          </h2>
          <div className="mt-6 grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
            {data.doctors.map((d) => (
              <DoctorCard key={d.slug} d={d} />
            ))}
          </div>
        </section>
      ) : null}

      {others.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <h2 className="text-xl font-semibold text-foreground">Related treatment costs</h2>
          <ul className="mt-3 flex flex-wrap gap-3 text-sm">
            {others.map((p) => (
              <li key={p.slug}>
                <Link
                  to="/treatment-cost/$slug"
                  params={{ slug: p.slug }}
                  className="rounded-full border border-border px-4 py-2 text-primary hover:bg-muted"
                >
                  {p.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section id="enquire" className="mx-auto max-w-3xl scroll-mt-28 px-4 pb-20">
        <AppointmentForm
          type="cost_enquiry"
          title={`Know your ${page.name} cost`}
          subtitle="Send your reports and receive a written estimate from suitable hospitals."
          defaultTreatment={page.name}
        />
      </section>
    </>
  );
}
