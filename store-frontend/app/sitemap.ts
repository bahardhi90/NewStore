import type { MetadataRoute } from "next";

import { getCategories, getCollections, getProducts } from "@/lib/api/catalog";
import { SITE_URL } from "@/lib/env";

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages = ["", "/stores", "/about", "/contact", "/faq", "/returns"].map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: "weekly" as const,
    priority: path === "" ? 1 : 0.5,
  }));

  try {
    const [categories, collections] = await Promise.all([getCategories(), getCollections()]);
    const products = [];
    for (let page = 1; page <= 20; page++) {
      const result = await getProducts({ page, page_size: 48 });
      products.push(...result.results);
      if (!result.next) break;
    }
    return [
      ...staticPages,
      ...categories.map((c) => ({ url: `${SITE_URL}/category/${c.slug}`, changeFrequency: "daily" as const, priority: 0.8 })),
      ...collections.map((c) => ({ url: `${SITE_URL}/collection/${c.slug}`, changeFrequency: "weekly" as const, priority: 0.7 })),
      ...products.map((p) => ({ url: `${SITE_URL}/product/${p.slug}`, changeFrequency: "weekly" as const, priority: 0.6 })),
    ];
  } catch {
    return staticPages;
  }
}
