import type { ProductQuery } from "@/types/api";

export type SearchParams = Record<string, string | string[] | undefined>;

const ORDERINGS = ["newest", "price", "-price", "-discount_percent", "popular"] as const;

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
const num = (v: string | undefined) => {
  if (!v) return undefined;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
};

/** URL search params -> API query (only whitelisted keys). */
export function parseListingParams(sp: SearchParams): ProductQuery {
  const ordering = first(sp.ordering);
  return {
    on_sale: first(sp.on_sale) === "true" || undefined,
    search: first(sp.search)?.trim() || undefined,
    size: first(sp.size) || undefined,
    color: first(sp.color) || undefined,
    min_price: num(first(sp.min_price)),
    max_price: num(first(sp.max_price)),
    ordering: ORDERINGS.includes(ordering as (typeof ORDERINGS)[number]) ? (ordering as ProductQuery["ordering"]) : undefined,
    page: Math.max(1, Number(first(sp.page)) || 1),
  };
}

/** Build a listing URL keeping current filters, with overrides. */
export function listingHref(basePath: string, sp: SearchParams, overrides: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(sp)) {
    const v = first(value);
    if (v) params.set(key, v);
  }
  for (const [key, value] of Object.entries(overrides)) {
    if (value === undefined || value === "" || (key === "page" && value === 1)) params.delete(key);
    else params.set(key, String(value));
  }
  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}
