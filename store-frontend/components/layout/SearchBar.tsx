"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { SearchIcon } from "@/components/ui/icons";
import { SmartImage } from "@/components/ui/SmartImage";
import { Spinner } from "@/components/ui/Spinner";
import { M } from "@/constants/messages";
import { searchApi } from "@/lib/api/shop";
import { formatPrice, toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";

const MIN_LETTERS = 2;
const MAX_SUGGESTIONS = 5;
const TYPING_PAUSE_MS = 250; // wait until the user stops typing before asking the server

/** Search box with a dropdown of matching products while typing (an accessible combobox). */
export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(-1);
  const boxRef = useRef<HTMLDivElement>(null);
  const inputId = useId(); // the bar appears in both the header and the drawer
  const listId = `${inputId}-list`;

  const term = query.trim();
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(term), TYPING_PAUSE_MS);
    return () => clearTimeout(timer);
  }, [term]);

  const ready = debounced.length >= MIN_LETTERS && debounced === term;
  const suggestions = useQuery({
    queryKey: ["search-suggestions", debounced],
    queryFn: () => searchApi.suggest(debounced, MAX_SUGGESTIONS),
    enabled: debounced.length >= MIN_LETTERS,
    staleTime: 60_000,
  });
  const products = ready ? (suggestions.data?.results ?? []) : [];
  const showList = open && term.length >= MIN_LETTERS;

  // Close when clicking anywhere else on the page
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  function goToResults() {
    setOpen(false);
    if (term) router.push(`/search?search=${encodeURIComponent(term)}`);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const product = products[highlighted];
    if (product) {
      setOpen(false);
      router.push(`/product/${product.slug}`);
    } else goToResults();
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!showList || products.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlighted((i) => (i + 1) % products.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlighted((i) => (i <= 0 ? products.length - 1 : i - 1));
    }
  }

  return (
    <div ref={boxRef} className="relative">
      <form role="search" onSubmit={onSubmit} className="relative">
        <label htmlFor={inputId} className="sr-only">
          {M.nav.search}
        </label>
        <input
          id={inputId}
          type="search"
          role="combobox"
          autoComplete="off"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={highlighted >= 0 && showList ? `${listId}-${highlighted}` : undefined}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setHighlighted(-1);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={M.nav.searchPlaceholder}
          className="border-line bg-surface focus:border-ink h-10 w-full rounded-full border ps-4 pe-10 text-sm focus:outline-none"
        />
        <button
          type="submit"
          className="hover:bg-sand absolute end-1 top-1 flex size-8 items-center justify-center rounded-full"
          aria-label={M.nav.search}
        >
          <SearchIcon className="size-4" />
        </button>
      </form>

      {showList && (
        <div className="rounded-card border-line bg-surface absolute inset-x-0 top-full z-50 mt-2 overflow-hidden border shadow-xl">
          {!ready || suggestions.isFetching ? (
            <div className="flex justify-center p-4" aria-live="polite">
              <Spinner className="size-5" />
            </div>
          ) : products.length === 0 ? (
            <p className="text-muted p-4 text-sm" aria-live="polite">
              {M.nav.noSuggestions}
            </p>
          ) : (
            <ul id={listId} role="listbox" aria-label={M.nav.suggestions} className="py-1">
              {products.map((product, i) => (
                <li key={product.id} id={`${listId}-${i}`} role="option" aria-selected={i === highlighted}>
                  <Link
                    href={`/product/${product.slug}`}
                    onClick={() => setOpen(false)}
                    onMouseEnter={() => setHighlighted(i)}
                    className={cn("flex items-center gap-3 px-3 py-2", i === highlighted && "bg-sand")}
                  >
                    <span className="bg-sand relative aspect-[4/5] w-10 shrink-0 overflow-hidden rounded-md">
                      <SmartImage src={product.image} alt="" fill sizes="40px" className="object-cover" />
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm">{product.title}</span>
                    <span className="flex shrink-0 flex-col items-end text-xs">
                      <span className="font-bold">{formatPrice(product.final_price)}</span>
                      {product.discount_percent > 0 && <span className="text-sale">{toFaDigits(product.discount_percent)}٪ تخفیف</span>}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            onClick={goToResults}
            className="border-line text-brand hover:bg-sand w-full border-t px-3 py-2.5 text-start text-sm font-medium"
          >
            {M.nav.allResults(term)}
          </button>
        </div>
      )}
    </div>
  );
}
