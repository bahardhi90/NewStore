"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/Button";
import { FilterIcon } from "@/components/ui/icons";
import { Modal } from "@/components/ui/Modal";
import { M } from "@/constants/messages";
import { formatPrice, toEnDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ProductFilterOptions } from "@/types/api";

const csv = (v: string | null) => (v ? v.split(",").filter(Boolean) : []);

/** Filters synced to URL query params. Desktop: sidebar. Mobile: drawer. */
export function FiltersPanel({ options }: { options: ProductFilterOptions }) {
  const [open, setOpen] = useState(false);
  const params = useSearchParams();
  const activeCount = ["size", "color", "on_sale", "min_price", "max_price"].filter((k) => params.get(k)).length;

  return (
    <>
      <div className="lg:hidden">
        <Button variant="outline" size="sm" onClick={() => setOpen(true)} icon={<FilterIcon className="size-4" />}>
          {M.listing.filters}
          {activeCount > 0 && <span className="bg-ink rounded-full px-1.5 text-xs text-white">{activeCount}</span>}
        </Button>
        <Modal open={open} onClose={() => setOpen(false)} title={M.listing.filters} variant="side">
          <div className="p-5">
            <FilterForm options={options} onDone={() => setOpen(false)} />
          </div>
        </Modal>
      </div>
      <aside className="sticky top-32 hidden w-64 shrink-0 lg:block" aria-label={M.listing.filters}>
        <FilterForm options={options} />
      </aside>
    </>
  );
}

function FilterForm({ options, onDone }: { options: ProductFilterOptions; onDone?: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [pending, startTransition] = useTransition();

  const sizes = csv(params.get("size"));
  const colors = csv(params.get("color"));
  const [minPrice, setMinPrice] = useState(params.get("min_price") ?? "");
  const [maxPrice, setMaxPrice] = useState(params.get("max_price") ?? "");

  function update(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params.toString());
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    next.delete("page");
    const q = next.toString();
    startTransition(() => router.push(q ? `${pathname}?${q}` : pathname, { scroll: false }));
  }

  function toggle(key: "size" | "color", list: string[], value: string) {
    const nextList = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
    update({ [key]: nextList.join(",") || null });
  }

  const chip = (active: boolean) =>
    cn(
      "rounded-lg border px-3 py-1.5 text-sm transition",
      active ? "border-ink bg-ink text-white" : "border-line bg-surface hover:border-ink",
    );

  return (
    <div className={cn("flex flex-col gap-6", pending && "opacity-60")}>
      <label className="flex cursor-pointer items-center justify-between gap-3 text-sm font-medium">
        {M.listing.onSaleOnly}
        <input
          type="checkbox"
          className="accent-ink size-5"
          checked={params.get("on_sale") === "true"}
          onChange={(e) => update({ on_sale: e.target.checked ? "true" : null })}
        />
      </label>

      {options.sizes && options.sizes.length > 0 && (
        <fieldset>
          <legend className="mb-3 text-sm font-bold">{M.product.size}</legend>
          <div className="flex flex-wrap gap-2">
            {options.sizes.map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={sizes.includes(s)}
                className={chip(sizes.includes(s))}
                onClick={() => toggle("size", sizes, s)}
              >
                {s}
              </button>
            ))}
          </div>
        </fieldset>
      )}

      {options.colors && options.colors.length > 0 && (
        <fieldset>
          <legend className="mb-3 text-sm font-bold">{M.product.color}</legend>
          <div className="flex flex-wrap gap-2">
            {options.colors.map((c) => (
              <button
                key={c.name}
                type="button"
                aria-pressed={colors.includes(c.name ?? "")}
                className={cn(chip(colors.includes(c.name ?? "")), "flex items-center gap-2")}
                onClick={() => toggle("color", colors, c.name ?? "")}
              >
                <span className="size-3.5 rounded-full ring-1 ring-black/10" style={{ backgroundColor: c.hex ?? "#ccc" }} />
                {c.name}
              </button>
            ))}
          </div>
        </fieldset>
      )}

      <fieldset>
        <legend className="mb-3 text-sm font-bold">{M.listing.priceRange}</legend>
        {options.min_price != null && options.max_price != null && (
          <p className="text-muted mb-2 text-xs">
            {formatPrice(options.min_price)} – {formatPrice(options.max_price)}
          </p>
        )}
        <form
          className="flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            update({
              min_price: toEnDigits(minPrice).replace(/\D/g, "") || null,
              max_price: toEnDigits(maxPrice).replace(/\D/g, "") || null,
            });
            onDone?.();
          }}
        >
          <div className="flex gap-2">
            <input
              inputMode="numeric"
              aria-label={M.listing.minPrice}
              placeholder={M.listing.minPrice}
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              className="border-line bg-surface focus:border-ink h-10 w-full rounded-lg border px-2 text-sm focus:outline-none"
            />
            <input
              inputMode="numeric"
              aria-label={M.listing.maxPrice}
              placeholder={M.listing.maxPrice}
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              className="border-line bg-surface focus:border-ink h-10 w-full rounded-lg border px-2 text-sm focus:outline-none"
            />
          </div>
          <Button type="submit" variant="outline" size="sm">
            {M.listing.apply}
          </Button>
        </form>
      </fieldset>

      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          setMinPrice("");
          setMaxPrice("");
          update({ size: null, color: null, on_sale: null, min_price: null, max_price: null });
          onDone?.();
        }}
      >
        {M.listing.clear}
      </Button>
    </div>
  );
}
