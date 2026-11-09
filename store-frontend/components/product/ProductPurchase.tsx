"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Price } from "@/components/ui/Price";
import { QuantityInput } from "@/components/ui/QuantityInput";
import { M } from "@/constants/messages";
import { useCart } from "@/hooks/useCart";
import { toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import { MAX_QUANTITY } from "@/store/cartStore";
import { toast, useUi } from "@/store/uiStore";
import type { ProductDetail } from "@/types/api";

import { useProductColor } from "./ProductColor";
import { SizeGuideButton, type SizeGuideContent } from "./SizeGuide";

export function ProductPurchase({ product, sizeGuide }: { product: ProductDetail; sizeGuide: SizeGuideContent }) {
  const { add } = useCart();
  const openMiniCart = useUi((s) => s.openMiniCart);

  const colors = useMemo(() => {
    const map = new Map<string, string | null>();
    for (const v of product.variants) if (!map.has(v.color)) map.set(v.color, v.color_hex ?? null);
    return [...map.entries()].map(([name, hex]) => ({ name, hex }));
  }, [product.variants]);
  const sizes = useMemo(() => [...new Set(product.variants.map((v) => v.size))], [product.variants]);

  const firstAvailable = product.variants.find((v) => v.stock > 0);
  const { color, setColor } = useProductColor();
  const [size, setSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);

  const variant = product.variants.find((v) => v.color === color && v.size === size) ?? null;
  const stockFor = (s: string, c: string | null) => product.variants.find((v) => v.size === s && v.color === c)?.stock ?? 0;
  const colorHasStock = (c: string) => product.variants.some((v) => v.color === c && v.stock > 0);
  const allSoldOut = !firstAvailable;
  const maxQty = variant ? Math.max(1, Math.min(variant.stock, MAX_QUANTITY)) : MAX_QUANTITY;

  async function onAdd() {
    if (!variant) {
      toast.error(M.product.chooseVariant);
      return;
    }
    setAdding(true);
    const ok = await add({
      variant,
      quantity,
      product: { id: product.id, title: product.title, slug: product.slug, image: product.image },
      base_price: product.base_price,
      discount_percent: product.discount_percent,
      final_price: product.final_price,
    });
    setAdding(false);
    if (ok) {
      toast.success(M.product.added);
      openMiniCart();
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Price
        basePrice={product.base_price}
        finalPrice={product.final_price}
        discountPercent={product.discount_percent}
        size="lg"
        showBadge
      />

      <fieldset>
        <legend className="mb-2 text-sm font-medium">
          {M.product.color}: <span className="text-muted">{color ?? "—"}</span>
        </legend>
        <div className="flex flex-wrap gap-2">
          {colors.map((c) => {
            const available = colorHasStock(c.name);
            return (
              <button
                key={c.name}
                type="button"
                onClick={() => {
                  setColor(c.name);
                  if (size && stockFor(size, c.name) === 0) setSize(null);
                  setQuantity(1);
                }}
                aria-pressed={color === c.name}
                disabled={!available}
                title={c.name}
                className={cn(
                  "flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition",
                  color === c.name ? "border-ink ring-ink ring-1" : "border-line hover:border-ink-soft",
                  !available && "cursor-not-allowed line-through opacity-40",
                )}
              >
                <span className="size-4 rounded-full ring-1 ring-black/10" style={{ backgroundColor: c.hex ?? "#ccc" }} />
                {c.name}
              </button>
            );
          })}
        </div>
      </fieldset>

      <fieldset>
        <div className="mb-2 flex items-center justify-between">
          <legend className="text-sm font-medium">{M.product.size}</legend>
          <SizeGuideButton guide={sizeGuide} />
        </div>
        <div className="flex flex-wrap gap-2">
          {sizes.map((s) => {
            const stock = stockFor(s, color);
            return (
              <button
                key={s}
                type="button"
                onClick={() => {
                  setSize(s);
                  setQuantity(1);
                }}
                disabled={stock === 0}
                aria-pressed={size === s}
                aria-label={stock === 0 ? `${s} - ${M.product.outOfStock}` : s}
                className={cn(
                  "h-11 min-w-12 rounded-lg border px-3 text-sm font-medium transition",
                  size === s ? "border-ink bg-ink text-white" : "border-line bg-surface hover:border-ink",
                  stock === 0 && "bg-sand text-muted hover:border-line cursor-not-allowed line-through opacity-60",
                )}
              >
                {s}
              </button>
            );
          })}
        </div>
        {variant && variant.stock > 0 && variant.stock <= 3 && (
          <p className="text-warning mt-2 text-xs">{M.product.onlyLeft(toFaDigits(variant.stock))}</p>
        )}
      </fieldset>

      <div className="flex flex-wrap items-center gap-3">
        <QuantityInput value={quantity} onChange={setQuantity} max={maxQty} disabled={allSoldOut} />
        <Button size="lg" className="flex-1" onClick={onAdd} loading={adding} disabled={allSoldOut}>
          {allSoldOut ? M.product.outOfStock : M.product.addToCart}
        </Button>
      </div>
      {!variant && !allSoldOut && <p className="text-muted -mt-3 text-xs">{M.product.selectSize}</p>}
    </div>
  );
}
