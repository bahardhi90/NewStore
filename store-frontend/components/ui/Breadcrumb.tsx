import Link from "next/link";

import { M } from "@/constants/messages";

export type Crumb = { label: string; href?: string };

export function Breadcrumb({ items }: { items: Crumb[] }) {
  const all: Crumb[] = [{ label: M.common.breadcrumbHome, href: "/" }, ...items];
  return (
    <nav aria-label="مسیر صفحه" className="text-muted text-xs">
      <ol className="flex flex-wrap items-center gap-1.5">
        {all.map((item, i) => (
          <li key={`${item.label}-${i}`} className="flex items-center gap-1.5">
            {i > 0 && <span aria-hidden="true">/</span>}
            {item.href && i < all.length - 1 ? (
              <Link href={item.href} className="hover:text-ink">
                {item.label}
              </Link>
            ) : (
              <span aria-current={i === all.length - 1 ? "page" : undefined} className="text-ink-soft">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
