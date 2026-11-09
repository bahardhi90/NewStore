"use client";

import { useState } from "react";

import { ChevronIcon } from "@/components/ui/icons";
import { Modal } from "@/components/ui/Modal";
import { SmartImage } from "@/components/ui/SmartImage";
import { cn } from "@/lib/utils";
import type { ProductImage } from "@/types/api";

import { useProductColor } from "./ProductColor";

/** Previous/next buttons over a picture. In RTL "next" sits on the left. */
function Arrows({ onPrev, onNext, className }: { onPrev: () => void; onNext: () => void; className?: string }) {
  const button =
    "bg-surface/90 hover:bg-surface absolute top-1/2 flex size-10 -translate-y-1/2 items-center justify-center rounded-full shadow ring-1 ring-black/5";
  return (
    <>
      <button type="button" onClick={onPrev} className={cn(button, "start-3", className)} aria-label="تصویر قبلی">
        <ChevronIcon className="size-5 rotate-180" />
      </button>
      <button type="button" onClick={onNext} className={cn(button, "end-3", className)} aria-label="تصویر بعدی">
        <ChevronIcon className="size-5" />
      </button>
    </>
  );
}

export function Gallery({ images, title }: { images: ProductImage[]; title: string }) {
  const list: ProductImage[] = images.length ? images : [{ image: "", alt: title }];
  const { color } = useProductColor();
  const imageFor = (c: string | null) =>
    Math.max(
      0,
      list.findIndex((img) => c && img.color === c),
    );

  const [active, setActive] = useState(() => imageFor(color));
  const [shownColor, setShownColor] = useState(color);
  const [zoomOpen, setZoomOpen] = useState(false);
  const [origin, setOrigin] = useState("50% 50%");
  const [hovering, setHovering] = useState(false);

  // A color button was clicked: jump to that color's first picture (if one is assigned in admin)
  if (color !== shownColor) {
    setShownColor(color);
    if (list.some((img) => img.color === color)) setActive(imageFor(color));
  }
  const current = list[active];
  const hasMany = list.length > 1;

  const show = (index: number) => setActive((index + list.length) % list.length); // wraps around
  const prev = () => show(active - 1);
  const next = () => show(active + 1);

  return (
    <div className="flex flex-col-reverse gap-3 md:flex-row-reverse md:items-start">
      <div className="flex gap-2 overflow-x-auto md:flex-col" role="tablist" aria-label="تصاویر محصول">
        {list.map((img, i) => (
          <button
            key={`${img.image}-${i}`}
            type="button"
            role="tab"
            aria-selected={i === active}
            onClick={() => setActive(i)}
            className={cn(
              "relative aspect-[4/5] w-16 shrink-0 overflow-hidden rounded-lg ring-2 transition md:w-20",
              i === active ? "ring-ink" : "hover:ring-line ring-transparent",
            )}
          >
            <SmartImage src={img.image || null} alt={img.alt || `${title} ${i + 1}`} fill sizes="80px" className="object-cover" />
          </button>
        ))}
      </div>
      <div
        className="relative w-full"
        onKeyDown={(e) => {
          if (!hasMany) return;
          if (e.key === "ArrowLeft") next(); // RTL: left moves forward
          if (e.key === "ArrowRight") prev();
        }}
      >
        <button
          type="button"
          className="rounded-card bg-sand relative block aspect-[4/5] w-full cursor-zoom-in overflow-hidden"
          onClick={() => setZoomOpen(true)}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => setHovering(false)}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            setOrigin(`${((e.clientX - rect.left) / rect.width) * 100}% ${((e.clientY - rect.top) / rect.height) * 100}%`);
          }}
          aria-label="بزرگ‌نمایی تصویر"
        >
          <SmartImage
            src={current.image || null}
            alt={current.alt || title}
            fill
            priority
            sizes="(min-width: 768px) 50vw, 100vw"
            className="object-cover transition-transform duration-200"
            style={{ transformOrigin: origin, transform: hovering ? "scale(1.8)" : "scale(1)" }}
          />
        </button>
        {hasMany && <Arrows onPrev={prev} onNext={next} />}
      </div>
      <Modal open={zoomOpen} onClose={() => setZoomOpen(false)} title={title} className="w-[min(92vw,48rem)]">
        <div className="bg-sand relative aspect-[4/5] w-full">
          <SmartImage src={current.image || null} alt={current.alt || title} fill sizes="90vw" className="object-contain" />
          {hasMany && <Arrows onPrev={prev} onNext={next} />}
        </div>
      </Modal>
    </div>
  );
}
