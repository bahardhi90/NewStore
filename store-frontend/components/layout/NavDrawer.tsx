"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, type MouseEvent } from "react";

import { ChevronIcon, MenuIcon } from "@/components/ui/icons";
import { Modal } from "@/components/ui/Modal";
import { M } from "@/constants/messages";
import { useUi } from "@/store/uiStore";
import type { Category, Collection } from "@/types/api";

import { SearchBar } from "./SearchBar";

const LINK = "block rounded-lg px-3 py-3 text-sm hover:bg-sand";

function CategoryLinks({ category, children }: { category: Category; children: Category[] }) {
  if (children.length === 0) {
    return (
      <Link href={`/category/${category.slug}`} className={LINK}>
        {category.name}
      </Link>
    );
  }
  return (
    <details className="group">
      <summary
        className="hover:bg-sand flex cursor-pointer list-none items-center justify-between rounded-lg px-3 py-3 text-sm [&::-webkit-details-marker]:hidden"
        aria-label={`${category.name}، ${M.nav.expand}`}
      >
        {category.name}
        <ChevronIcon className="size-4 -rotate-90 transition-transform group-open:rotate-90" />
      </summary>
      <div className="border-line ms-3 flex flex-col border-s ps-2">
        <Link href={`/category/${category.slug}`} className={LINK}>
          {M.nav.allProducts} {category.name}
        </Link>
        {children.map((child) => (
          <Link key={child.id} href={`/category/${child.slug}`} className={LINK}>
            {child.name}
          </Link>
        ))}
      </div>
    </details>
  );
}

/** Hamburger menu at every screen size: a drawer that slides in from the right (RTL start). */
export function NavDrawer({ categories, collections }: { categories: Category[]; collections: Collection[] }) {
  const open = useUi((s) => s.navDrawerOpen);
  const setOpen = useUi((s) => s.setNavDrawer);
  const pathname = usePathname();
  const topLevel = categories.filter((c) => c.parent === null);

  // Close the drawer after navigation
  useEffect(() => {
    setOpen(false);
  }, [pathname, setOpen]);

  // Links to the current page don't change the pathname, so close on the click too
  function onNavClick(event: MouseEvent<HTMLElement>) {
    if ((event.target as HTMLElement).closest("a")) setOpen(false);
  }

  return (
    <>
      <button
        type="button"
        className="hover:bg-sand flex size-10 shrink-0 items-center justify-center rounded-full"
        onClick={() => setOpen(true)}
        aria-label={M.nav.menu}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <MenuIcon className="size-6" />
      </button>
      <Modal open={open} onClose={() => setOpen(false)} title={M.nav.menu} variant="side">
        <div className="border-line border-b p-4 md:hidden">
          <SearchBar />
        </div>
        <nav aria-label={M.nav.menu} className="flex flex-col gap-1 p-4" onClick={onNavClick}>
          <Link href="/" className={LINK}>
            {M.nav.home}
          </Link>
          <p className="text-muted mt-3 px-3 text-xs font-bold">{M.nav.categories}</p>
          {topLevel.map((category) => (
            <CategoryLinks key={category.id} category={category}>
              {categories.filter((c) => c.parent === category.id)}
            </CategoryLinks>
          ))}
          {collections.length > 0 && <p className="text-muted mt-3 px-3 text-xs font-bold">{M.nav.collections}</p>}
          {collections.map((c) => (
            <Link key={c.id} href={`/collection/${c.slug}`} className={LINK}>
              {c.title}
            </Link>
          ))}
          <hr className="border-line my-3" />
          <Link href="/search?on_sale=true" className={`${LINK} text-sale`}>
            {M.nav.sale}
          </Link>
          <Link href="/stores" className={LINK}>
            {M.nav.stores}
          </Link>
          <Link href="/faq" className={LINK}>
            {M.nav.faq}
          </Link>
          <Link href="/contact" className={LINK}>
            {M.nav.contact}
          </Link>
        </nav>
      </Modal>
    </>
  );
}
