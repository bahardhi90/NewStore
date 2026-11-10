/**
 * Server-side catalog data (Server Components). Same function signatures for mock and real API;
 * switch with NEXT_PUBLIC_USE_MOCKS.
 */
import "server-only";

import { M } from "@/constants/messages";
import { uniqueFilterOptions } from "@/lib/filter-options";
import { ServerApiError, serverGet } from "@/lib/server/backend";
import type {
  Category,
  Collection,
  Home,
  Page,
  PaginatedProducts,
  ProductDetail,
  ProductFilterOptions,
  ProductQuery,
  ShippingMethod,
  SiteSettings,
  Store,
} from "@/types/api";

const REVALIDATE = { home: 60, catalog: 60, product: 60, static: 300 } as const;

function toSearch(query: Record<string, unknown>): URLSearchParams {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    search.set(key, String(value));
  }
  return search;
}

/** Never throws: the header and footer must render even if the API is down. */
export async function getSiteSettings(): Promise<SiteSettings> {
  try {
    return await serverGet<SiteSettings>("/site-settings/", undefined, REVALIDATE.catalog);
  } catch {
    return {
      brand_name: M.brand,
      tagline: M.tagline,
      logo: null,
      announcement_text: "",
      instagram_url: "",
      telegram_url: "",
      trust_badges: [],
      footer_columns: [],
      shipping_points: [],
      size_guide_note: "",
      size_charts: [],
    };
  }
}

const PAGE_TITLES: Record<Page["slug"], string> = {
  about: M.nav.about,
  contact: M.nav.contact,
  faq: M.nav.faq,
  returns: M.nav.returns,
};

/** Never throws: an empty page (title only) if the API is unreachable, e.g. during `next build`. */
export async function getPage(slug: Page["slug"]): Promise<Page> {
  try {
    return await serverGet<Page>(`/pages/${slug}/`, undefined, REVALIDATE.catalog);
  } catch {
    return { slug, title: PAGE_TITLES[slug], paragraphs: [], items: [] };
  }
}

export const getHome = () => serverGet<Home>("/home/", undefined, REVALIDATE.home);
export const getCategories = () => serverGet<Category[]>("/categories/", undefined, REVALIDATE.static);
export const getCollections = () => serverGet<Collection[]>("/collections/", undefined, REVALIDATE.static);
export const getStores = () => serverGet<Store[]>("/stores/", undefined, REVALIDATE.static);
export const getShippingMethods = () => serverGet<ShippingMethod[]>("/shipping-methods/", undefined, REVALIDATE.static);

export async function getCollection(slug: string): Promise<Collection | null> {
  return nullOn404(() => serverGet<Collection>(`/collections/${encodeURIComponent(slug)}/`, undefined, REVALIDATE.catalog));
}

export async function getProducts(query: ProductQuery = {}): Promise<PaginatedProducts> {
  try {
    return await serverGet<PaginatedProducts>("/products/", toSearch(query), REVALIDATE.catalog);
  } catch (error) {
    // Page number out of range -> empty page instead of an error screen
    if (error instanceof ServerApiError && error.status === 404) return { count: 0, next: null, previous: null, results: [] };
    throw error;
  }
}

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  return nullOn404(() => serverGet<ProductDetail>(`/products/${encodeURIComponent(slug)}/`, undefined, REVALIDATE.product));
}

export async function getProductFilters(query: Pick<ProductQuery, "category" | "collection" | "on_sale" | "search">) {
  const options = await serverGet<ProductFilterOptions>("/products/filters/", toSearch(query), REVALIDATE.catalog);
  return uniqueFilterOptions(options);
}

async function nullOn404<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof ServerApiError && error.status === 404) return null;
    throw error;
  }
}
