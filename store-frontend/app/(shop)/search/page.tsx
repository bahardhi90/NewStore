import type { Metadata } from "next";

import { Breadcrumb } from "@/components/ui/Breadcrumb";
import type { SearchParams } from "@/components/product/listing-params";
import { ProductListing } from "@/components/product/ProductListing";
import { M } from "@/constants/messages";

type Props = { searchParams: Promise<SearchParams> };

export const metadata: Metadata = {
  title: M.nav.search,
  robots: { index: false, follow: true },
};

export default async function SearchPage({ searchParams }: Props) {
  const sp = await searchParams;
  const q = typeof sp.search === "string" ? sp.search.trim() : "";
  const title = q ? M.listing.searchTitle(q) : sp.on_sale === "true" ? M.home.onSale : M.nav.allProducts;

  return (
    <div className="container-page flex flex-col gap-6 py-6">
      <Breadcrumb items={[{ label: title }]} />
      <h1 className="text-2xl font-black sm:text-3xl">{title}</h1>
      <ProductListing basePath="/search" searchParams={sp} scope={{}} />
    </div>
  );
}
