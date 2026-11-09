import type { Metadata } from "next";

import { getPage } from "@/lib/api/catalog";
import { toEnDigits, toFaDigits } from "@/lib/format";

export const revalidate = 60;

/** Phone numbers and emails typed in admin become tappable links. */
function linkFor(value: string): string | null {
  const plain = toEnDigits(value).trim();
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(plain)) return `mailto:${plain}`;
  if (/^\+?[\d\s-]{7,}$/.test(plain)) return `tel:${plain.replace(/[\s-]/g, "")}`;
  return null;
}

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getPage("contact")).title, alternates: { canonical: "/contact" } };
}

export default async function ContactPage() {
  const page = await getPage("contact");
  return (
    <div className="container-page flex max-w-3xl flex-col gap-6 py-10">
      <h1 className="text-3xl font-black">{page.title}</h1>
      {page.paragraphs.map((p, i) => (
        <p key={i} className="text-ink-soft leading-8 whitespace-pre-line">
          {p}
        </p>
      ))}
      {page.items.length > 0 && (
        <dl className="divide-line rounded-card bg-surface ring-line divide-y px-5 ring-1">
          {page.items.map((item, i) => {
            const href = linkFor(item.body);
            return (
              <div key={i} className="flex flex-col gap-1 py-4 sm:flex-row sm:justify-between">
                <dt className="text-muted text-sm">{item.heading}</dt>
                <dd className="font-medium">
                  {href ? (
                    <a href={href} className="ltr-nums hover:underline">
                      {toFaDigits(item.body)}
                    </a>
                  ) : (
                    item.body
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      )}
    </div>
  );
}
