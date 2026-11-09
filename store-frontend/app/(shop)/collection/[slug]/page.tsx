import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CollectionBanner } from "@/components/home/CollectionBanner";
import { Breadcrumb } from "@/components/ui/Breadcrumb";
import type { SearchParams } from "@/components/product/listing-params";
import { ProductListing } from "@/components/product/ProductListing";
import { M } from "@/constants/messages";
import { getCollection } from "@/lib/api/catalog";

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<SearchParams> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const collection = await getCollection(decodeURIComponent(slug));
  if (!collection) return {};
  return {
    title: collection.title,
    description: collection.description || collection.title,
    alternates: { canonical: `/collection/${collection.slug}` },
    openGraph: { images: collection.banner ? [collection.banner] : [] },
  };
}

export default async function CollectionPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const sp = await searchParams;
  const collection = await getCollection(decodeURIComponent(slug));
  if (!collection) notFound();

  return (
    <div className="container-page flex flex-col gap-6 py-6">
      <Breadcrumb items={[{ label: M.nav.collections }, { label: collection.title }]} />
      <h1 className="sr-only">{collection.title}</h1>
      <CollectionBanner collection={collection} asLink={false} />
      <ProductListing basePath={`/collection/${collection.slug}`} searchParams={sp} scope={{ collection: collection.slug }} />
    </div>
  );
}
