import type { Metadata } from "next";

import { ChevronDownIcon } from "@/components/ui/icons";
import { getPage } from "@/lib/api/catalog";

export const revalidate = 60;

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getPage("faq")).title, alternates: { canonical: "/faq" } };
}

export default async function FaqPage() {
  const page = await getPage("faq");
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: page.items.map((item) => ({
      "@type": "Question",
      name: item.heading,
      acceptedAnswer: { "@type": "Answer", text: item.body },
    })),
  };
  return (
    <div className="container-page flex max-w-3xl flex-col gap-6 py-10">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      <h1 className="text-3xl font-black">{page.title}</h1>
      {page.paragraphs.map((p, i) => (
        <p key={i} className="text-ink-soft leading-8 whitespace-pre-line">
          {p}
        </p>
      ))}
      <div className="flex flex-col gap-3">
        {page.items.map((item, i) => (
          <details key={i} className="group rounded-card bg-surface ring-line p-5 ring-1">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-bold">
              {item.heading}
              <ChevronDownIcon className="size-5 shrink-0 transition-transform group-open:rotate-180" />
            </summary>
            <p className="text-ink-soft mt-3 leading-8 whitespace-pre-line">{item.body}</p>
          </details>
        ))}
      </div>
    </div>
  );
}
