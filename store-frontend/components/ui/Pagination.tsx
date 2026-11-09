import Link from "next/link";

import { M } from "@/constants/messages";
import { toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";

type Props = {
  page: number;
  totalPages: number;
  /** Builds the href for a page number (keeps current filters). */
  hrefFor: (page: number) => string;
};

function range(page: number, total: number): (number | "…")[] {
  const pages = new Set([1, total, page - 1, page, page + 1].filter((p) => p >= 1 && p <= total));
  const sorted = [...pages].sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) out.push("…");
    out.push(p);
  });
  return out;
}

export function Pagination({ page, totalPages, hrefFor }: Props) {
  if (totalPages <= 1) return null;
  const item = "flex size-10 items-center justify-center rounded-lg text-sm";
  return (
    <nav aria-label={M.common.page} className="mt-10 flex items-center justify-center gap-1.5">
      {page > 1 ? (
        <Link href={hrefFor(page - 1)} className={cn(item, "hover:bg-sand w-auto px-3")} rel="prev">
          {M.common.previous}
        </Link>
      ) : null}
      {range(page, totalPages).map((p, i) =>
        p === "…" ? (
          <span key={`gap-${i}`} className={cn(item, "text-muted")}>
            …
          </span>
        ) : (
          <Link
            key={p}
            href={hrefFor(p)}
            aria-current={p === page ? "page" : undefined}
            className={cn(item, p === page ? "bg-ink text-white" : "hover:bg-sand")}
          >
            {toFaDigits(p)}
          </Link>
        ),
      )}
      {page < totalPages ? (
        <Link href={hrefFor(page + 1)} className={cn(item, "hover:bg-sand w-auto px-3")} rel="next">
          {M.common.next}
        </Link>
      ) : null}
    </nav>
  );
}
