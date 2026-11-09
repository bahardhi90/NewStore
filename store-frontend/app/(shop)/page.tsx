import { CategoryTiles } from "@/components/home/CategoryTiles";
import { BannerSlide, CollectionSlide, SectionSlide } from "@/components/home/HomeSlides";
import { HomeSwiper } from "@/components/home/HomeSwiper";
import { ProductCarousel } from "@/components/product/ProductCarousel";
import { M } from "@/constants/messages";
import { getHome, getSiteSettings } from "@/lib/api/catalog";
import type { Home } from "@/types/api";

export const revalidate = 60; // ISR

const EMPTY_HOME: Home = { banners: [], categories: [], on_sale: [], collection_highlight: null, newest: [] };
const MAX_CATEGORY_TILES = 6; // two rows still fit in one screen

/** If the API is unreachable (e.g. during `next build`), render an empty page; ISR retries in 60s. */
async function loadHome(): Promise<Home> {
  try {
    return await getHome();
  } catch {
    return EMPTY_HOME;
  }
}

export default async function HomePage() {
  const [home, site] = await Promise.all([loadHome(), getSiteSettings()]);

  return (
    <HomeSwiper withAnnouncement={Boolean(site.announcement_text)}>
      {home.banners.map((banner, i) => (
        <BannerSlide key={banner.id} banner={banner} priority={i === 0} />
      ))}

      {home.categories.length > 0 && (
        <SectionSlide title={M.home.categories}>
          <div className="mx-auto w-full max-w-4xl">
            <CategoryTiles categories={home.categories.slice(0, MAX_CATEGORY_TILES)} />
          </div>
        </SectionSlide>
      )}

      {home.on_sale.length > 0 && (
        <SectionSlide title={M.home.onSale} href="/search?on_sale=true">
          <ProductCarousel products={home.on_sale} label={M.home.onSale} />
        </SectionSlide>
      )}

      {home.collection_highlight && <CollectionSlide collection={home.collection_highlight.collection} />}

      {home.newest.length > 0 && (
        <SectionSlide title={M.home.newest} href="/search?ordering=newest">
          <ProductCarousel products={home.newest} label={M.home.newest} />
        </SectionSlide>
      )}
    </HomeSwiper>
  );
}
