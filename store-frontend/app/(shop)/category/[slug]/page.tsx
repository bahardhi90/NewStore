import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Breadcrumb } from "@/components/ui/Breadcrumb";
import type { SearchParams } from "@/components/product/listing-params";
import { ProductListing } from "@/components/product/ProductListing";
import { getCategories } from "@/lib/api/catalog";

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<SearchParams> };

async function findCategory(slug: string) {
  const categories = await getCategories();
  const category = categories.find((c) => c.slug === decodeURIComponent(slug));
  const parent = category?.parent ? categories.find((c) => c.id === category.parent) : undefined;
  return { category, parent };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const { category } = await findCategory(slug);
  if (!category) return {};
  return {
    title: category.name,
    description: `خرید ${category.name} مردانه با بهترین قیمت و ارسال سریع`,
    alternates: { canonical: `/category/${category.slug}` },
  };
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const sp = await searchParams;
  const { category, parent } = await findCategory(slug);
  if (!category) notFound();

  return (
    <div className="container-page flex flex-col gap-6 py-6">
      <Breadcrumb items={[...(parent ? [{ label: parent.name, href: `/category/${parent.slug}` }] : []), { label: category.name }]} />
      <h1 className="text-2xl font-black sm:text-3xl">{category.name}</h1>
      <ProductListing basePath={`/category/${category.slug}`} searchParams={sp} scope={{ category: category.slug }} />
    </div>
  );
}
