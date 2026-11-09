import { getCategories, getCollections, getSiteSettings } from "@/lib/api/catalog";
import type { Category, Collection } from "@/types/api";

import { HeaderActions } from "./HeaderActions";
import { Logo } from "./Logo";
import { NavDrawer } from "./NavDrawer";
import { SearchBar } from "./SearchBar";

async function loadMenu(): Promise<{ categories: Category[]; collections: Collection[] }> {
  try {
    const [categories, collections] = await Promise.all([getCategories(), getCollections()]);
    return { categories, collections };
  } catch {
    return { categories: [], collections: [] }; // header must render even if the API is down
  }
}

export async function Header() {
  const [{ categories, collections }, site] = await Promise.all([loadMenu(), getSiteSettings()]);

  return (
    // Glass effect: 72% white with a 14px blur of whatever scrolls underneath
    <header className="border-line sticky top-0 z-40 border-b bg-white/72 backdrop-blur-[14px]">
      {site.announcement_text && <div className="bg-fabric py-2 text-center text-xs text-white">{site.announcement_text}</div>}
      <div className="container-page flex h-16 items-center gap-2 sm:gap-4">
        <NavDrawer categories={categories} collections={collections} />
        <Logo site={site} />
        <div className="ms-auto hidden w-full max-w-xs md:block">
          <SearchBar />
        </div>
        <HeaderActions />
      </div>
    </header>
  );
}
