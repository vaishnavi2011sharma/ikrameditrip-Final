import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { AppointmentForm } from "@/components/site/AppointmentForm";
import { Breadcrumbs, DoctorCard, HospitalPhoto, TextBlock } from "@/components/site/cards";
import { CostGuideCards, RichContent } from "@/components/site/RichContent";
import { PROSTHETIC_IMAGES } from "@/data/prosthetic-images";
import { DEPT_CONTENT } from "@/data/dept-content";
import { getDepartment, getDepartmentExtras } from "@/lib/data-fns";
import { canonical } from "@/lib/search";

export const Route = createFileRoute("/services_/$slug")({
  loader: async ({ params }) => {
    const department = await getDepartment({ data: { slug: params.slug } });
    if (!department) throw notFound();
    const extras = await getDepartmentExtras({ data: { slug: params.slug } });
    return { department, extras };
  },
  head: ({ loaderData }) => {
    const x = loaderData?.department;
    if (!x) return {};
    const title = x.seo_title || `${x.name} Treatment in India - Doctors, Hospitals & Cost | Ikra Meditrip`;
    const lead = DEPT_CONTENT[x.slug]?.blocks.find((b) => b.t === "p");
    const desc = x.seo_description || x.summary || (lead && lead.t === "p" ? lead.text.replace(/\*\*|\[([^\]]+)\]\([^)]*\)/g, "$1") : "") || `${x.name} specialists and hospitals in India. Get a free treatment cost estimate from Ikra Meditrip.`;
    return {
      meta: [
        { title },
        { name: "description", content: desc.slice(0, 200) },
        { property: "og:title", content: title },
        { property: "og:description", content: desc.slice(0, 200) },
      ],
      links: [{ rel: "canonical", href: canonical(`/services/${x.slug}`) }],
    };
  },
  component: DepartmentPage,
});

function DepartmentPage() {
  const { department: x, extras } = Route.useLoaderData();
  const content = DEPT_CONTENT[x.slug];
  const hasContent = !!content && content.blocks.length > 0;
  const topHospitals = extras.hospitals.length ? extras.hospitals : x.hospitals;
  const topDoctors = hasContent && extras.doctors.length ? extras.doctors : x.doctors;
  return (
    <>
      <Breadcrumbs items={[{ label: "Treatments", to: "/services" }, { label: x.name }]} />
      <section className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">{x.name}</h1>
        <div className="mt-4 max-w-4xl">
          {hasContent ? <RichContent blocks={content!.blocks} /> : <TextBlock text={x.body || x.summary} />}
        </div>
      </section>

      {x.slug === "prosthetic-and-artificial-body-parts" && PROSTHETIC_IMAGES.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10" aria-label="Prosthetic photographs">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {PROSTHETIC_IMAGES.map((im) => (
              <figure key={im.src} className="overflow-hidden rounded-2xl border border-border bg-card">
                <img src={im.src} alt={im.alt} width={im.width} height={im.height} loading="lazy" decoding="async" className="h-auto w-full object-cover" />
                <figcaption className="px-3 py-2 text-xs text-muted-foreground">{im.credit}</figcaption>
              </figure>
            ))}
          </div>
        </section>
      ) : null}

      <CostGuideCards deptSlug={x.slug} />

      {x.treatments.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">Surgeries & treatments</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {x.treatments.map((t) => (
              <Link key={t.slug} to="/treatments/$slug" params={{ slug: t.slug }}
                className="rounded-2xl border border-border bg-card p-5 shadow-card hover:shadow-lift">
                <h3 className="font-semibold text-foreground">{t.name}</h3>
                {t.summary ? <p className="mt-1 text-sm text-muted-foreground">{t.summary}</p> : null}
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {topHospitals.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{hasContent && content!.hospitalsHeading && extras.hospitals.length ? content!.hospitalsHeading : `Hospitals for ${x.name}`}</h2>
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {topHospitals.map((h) => (
              <Link key={h.slug} to="/hospitals/$slug" params={{ slug: h.slug }}
                className="overflow-hidden rounded-2xl border border-border bg-card shadow-card hover:shadow-lift">
                <HospitalPhoto h={{ ...h, is_placeholder_image: h.image_url ? 0 : 1 }} className="h-36 w-full" />
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-foreground">{h.name}</h3>
                  <p className="text-xs text-muted-foreground">{h.city}, {h.country}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {topDoctors.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-10">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{hasContent ? `Top doctors for ${x.name}` : `${x.name} doctors`}</h2>
            {hasContent && extras.doctorCount > topDoctors.length ? (
              <Link to="/doctors" search={{ department: x.slug }} className="text-sm font-semibold text-primary hover:underline">View all {extras.doctorCount} doctors →</Link>
            ) : null}
          </div>
          <div className="mt-6 grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
            {topDoctors.map((d) => (
              <DoctorCard key={d.slug} d={d} />
            ))}
          </div>
        </section>
      ) : null}

      <section id="enquire" className="mx-auto max-w-3xl scroll-mt-28 px-4 pb-20">
        <AppointmentForm
          type="cost_enquiry"
          title={`Know your ${x.name} treatment cost`}
          subtitle="Send your reports and receive a written estimate from suitable hospitals."
          defaultTreatment={x.name}
        />
      </section>
    </>
  );
}
