"use client";

import useEmblaCarousel from "embla-carousel-react";
import { useCallback } from "react";

import { ChevronIcon } from "@/components/ui/icons";
import type { ProductListItem } from "@/types/api";

import { ProductCard } from "./ProductCard";

export function ProductCarousel({ products, label }: { products: ProductListItem[]; label: string }) {
  const [ref, api] = useEmblaCarousel({ direction: "rtl", align: "start", dragFree: true });
  const prev = useCallback(() => api?.scrollPrev(), [api]);
  const next = useCallback(() => api?.scrollNext(), [api]);

  return (
    <div className="relative" role="region" aria-roledescription="carousel" aria-label={label}>
      <div className="overflow-hidden" ref={ref}>
        <div className="-ms-4 flex">
          {products.map((product) => (
            <div key={product.id} className="min-w-0 shrink-0 grow-0 basis-1/2 ps-4 md:basis-1/3 lg:basis-1/4">
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      </div>
      <button
        type="button"
        onClick={prev}
        className="bg-surface ring-line absolute -start-4 top-1/3 hidden size-10 items-center justify-center rounded-full shadow ring-1 md:flex"
        aria-label="قبلی"
      >
        <ChevronIcon className="size-5 rotate-180" />
      </button>
      <button
        type="button"
        onClick={next}
        className="bg-surface ring-line absolute -end-4 top-1/3 hidden size-10 items-center justify-center rounded-full shadow ring-1 md:flex"
        aria-label="بعدی"
      >
        <ChevronIcon className="size-5" />
      </button>
    </div>
  );
}
