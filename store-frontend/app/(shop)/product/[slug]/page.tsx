import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { SectionHeader } from "@/components/home/SectionHeader";
import { TrustBadges } from "@/components/layout/TrustBadges";
import { Gallery } from "@/components/product/Gallery";
import { ProductGrid } from "@/components/product/ProductGrid";
import { ProductColorProvider } from "@/components/product/ProductColor";
import { ProductPurchase } from "@/components/product/ProductPurchase";
import { ProductTabs } from "@/components/product/ProductTabs";
import { Breadcrumb } from "@/components/ui/Breadcrumb";
import { M } from "@/constants/messages";
import { getProduct, getProducts, getSiteSettings } from "@/lib/api/catalog";
import { SITE_URL } from "@/lib/env";
import { initialColor } from "@/lib/product";

type Props = { params: Promise<{ slug: string }> };

export const revalidate = 60;

function absolute(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  return url.startsWith("http") ? url : `${SITE_URL}${url}`;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(decodeURIComponent(slug));
  if (!product) return {};
  const description = product.description.split("\n")[0].slice(0, 160);
  return {
    title: product.title,
    description,
    alternates: { canonical: `/product/${product.slug}` },
    openGraph: {
      title: product.title,
      description,
      images: product.images.map((img) => absolute(img.image)).filter(Boolean) as string[],
    },
  };
}

export default async function ProductPage({ params }: Props) {
  const { slug } = await params;
  const product = await getProduct(decodeURIComponent(slug));
  if (!product) notFound();

  const [relatedPage, site] = await Promise.all([getProducts({ category: product.category.slug, page_size: 5 }), getSiteSettings()]);
  const related = relatedPage.results.filter((p) => p.id !== product.id).slice(0, 4);
  const inStock = product.variants.some((v) => v.stock > 0);

  // Structured data for Google (price in IRR: Toman × 10)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.title,
    description: product.description,
    image: product.images.map((img) => absolute(img.image)),
    sku: String(product.id),
    category: product.category.name,
    offers: {
      "@type": "Offer",
      url: `${SITE_URL}/product/${product.slug}`,
      priceCurrency: "IRR",
      price: product.final_price * 10,
      availability: inStock ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
    },
  };

  return (
    <div className="container-page flex flex-col gap-12 py-6">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      <Breadcrumb items={[{ label: product.category.name, href: `/category/${product.category.slug}` }, { label: product.title }]} />

      <ProductColorProvider initial={initialColor(product)}>
        <div className="grid gap-8 md:grid-cols-2 lg:gap-14">
          <Gallery images={product.images} title={product.title} />
          <div className="flex flex-col gap-6">
            <h1 className="text-2xl leading-snug font-black sm:text-3xl">{product.title}</h1>
            <ProductPurchase product={product} sizeGuide={{ note: site.size_guide_note, charts: site.size_charts }} />
            <TrustBadges compact className="grid-cols-2 lg:grid-cols-2" />
            <ProductTabs description={product.description} shippingPoints={site.shipping_points} />
          </div>
        </div>
      </ProductColorProvider>

      {related.length > 0 && (
        <section>
          <SectionHeader title={M.product.related} href={`/category/${product.category.slug}`} />
          <ProductGrid products={related} />
        </section>
      )}
    </div>
  );
}
