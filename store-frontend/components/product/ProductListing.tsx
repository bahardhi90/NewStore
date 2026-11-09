import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";
import { M } from "@/constants/messages";
import { getProductFilters, getProducts } from "@/lib/api/catalog";
import { toFaDigits } from "@/lib/format";
import type { ProductQuery } from "@/types/api";

import { FiltersPanel } from "./FiltersPanel";
import { listingHref, parseListingParams, type SearchParams } from "./listing-params";
import { ProductGrid } from "./ProductGrid";
import { SortSelect } from "./SortSelect";

const PAGE_SIZE = 12;

type Props = {
  basePath: string;
  searchParams: SearchParams;
  /** Fixed scope of this page (e.g. category or collection slug). */
  scope: Pick<ProductQuery, "category" | "collection">;
};

export async function ProductListing({ basePath, searchParams, scope }: Props) {
  const query = { ...parseListingParams(searchParams), ...scope, page_size: PAGE_SIZE };
  const [products, filters] = await Promise.all([
    getProducts(query),
    getProductFilters({ ...scope, on_sale: query.on_sale, search: query.search }),
  ]);
  const totalPages = Math.max(1, Math.ceil(products.count / PAGE_SIZE));

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <FiltersPanel options={filters} />
      <div className="min-w-0 flex-1">
        <div className="mb-5 flex items-center justify-between gap-3">
          <p className="text-muted text-sm">{M.listing.results(toFaDigits(products.count))}</p>
          <SortSelect />
        </div>
        {products.results.length === 0 ? (
          <EmptyState title={M.listing.empty} text={M.listing.emptyHint} />
        ) : (
          <>
            <ProductGrid products={products.results} priorityCount={4} />
            <Pagination page={query.page ?? 1} totalPages={totalPages} hrefFor={(page) => listingHref(basePath, searchParams, { page })} />
          </>
        )}
      </div>
    </div>
  );
}
