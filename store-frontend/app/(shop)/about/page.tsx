import type { Metadata } from "next";

import { TrustBadges } from "@/components/layout/TrustBadges";
import { getPage } from "@/lib/api/catalog";

export const revalidate = 60;

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getPage("about")).title, alternates: { canonical: "/about" } };
}

export default async function AboutPage() {
  const page = await getPage("about");
  return (
    <article className="container-page flex max-w-3xl flex-col gap-6 py-10">
      <h1 className="text-3xl font-black">{page.title}</h1>
      {page.paragraphs.map((p, i) => (
        <p key={i} className="text-ink-soft leading-8 whitespace-pre-line">
          {p}
        </p>
      ))}
      <TrustBadges className="mt-6" />
    </article>
  );
}
