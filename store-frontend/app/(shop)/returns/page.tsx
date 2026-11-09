import type { Metadata } from "next";

import { getPage } from "@/lib/api/catalog";

export const revalidate = 60;

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getPage("returns")).title, alternates: { canonical: "/returns" } };
}

export default async function ReturnsPage() {
  const page = await getPage("returns");
  return (
    <article className="container-page flex max-w-3xl flex-col gap-6 py-10">
      <h1 className="text-3xl font-black">{page.title}</h1>
      {page.paragraphs.map((p, i) => (
        <p key={i} className="text-ink-soft leading-8 whitespace-pre-line">
          {p}
        </p>
      ))}
      {page.items.map((section, i) => (
        <section key={i}>
          <h2 className="mb-2 text-lg font-bold">{section.heading}</h2>
          <p className="text-ink-soft leading-8 whitespace-pre-line">{section.body}</p>
        </section>
      ))}
    </article>
  );
}
