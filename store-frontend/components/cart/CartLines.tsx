"use client";

import Link from "next/link";

import { AlertIcon, TrashIcon } from "@/components/ui/icons";
import { QuantityInput } from "@/components/ui/QuantityInput";
import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import type { CartLineView } from "@/hooks/useCart";
import { formatPrice } from "@/lib/format";
import { MAX_QUANTITY } from "@/store/cartStore";

type Props = {
  items: CartLineView[];
  onQuantity: (key: number, quantity: number) => void;
  onRemove: (key: number) => void;
  disabled?: boolean;
  compact?: boolean;
};

export function CartLines({ items, onQuantity, onRemove, disabled, compact }: Props) {
  return (
    <ul className="divide-line divide-y">
      {items.map((item) => (
        <li key={item.key} className="flex gap-4 py-4">
          <Link
            href={`/product/${item.product.slug}`}
            className="bg-sand relative aspect-[4/5] w-20 shrink-0 overflow-hidden rounded-lg sm:w-24"
          >
            <SmartImage src={item.product.image} alt={item.product.title} fill sizes="96px" className="object-cover" />
          </Link>
          <div className="flex min-w-0 flex-1 flex-col gap-1.5">
            <div className="flex items-start justify-between gap-2">
              <Link href={`/product/${item.product.slug}`} className="line-clamp-2 text-sm font-medium hover:underline">
                {item.product.title}
              </Link>
              <button
                type="button"
                onClick={() => onRemove(item.key)}
                disabled={disabled}
                className="text-muted hover:bg-sand hover:text-sale rounded-md p-1"
                aria-label={`${M.cart.remove} ${item.product.title}`}
              >
                <TrashIcon className="size-4" />
              </button>
            </div>
            <p className="text-muted flex items-center gap-2 text-xs">
              <span>
                {M.product.size}: {item.variant.size}
              </span>
              <span aria-hidden="true">|</span>
              <span className="flex items-center gap-1">
                {item.variant.color_hex && (
                  <span className="ring-line size-3 rounded-full ring-1" style={{ backgroundColor: item.variant.color_hex }} />
                )}
                {item.variant.color}
              </span>
            </p>
            {item.warning && (
              <p className="text-warning flex items-center gap-1 text-xs">
                <AlertIcon className="size-3.5" />
                {item.warning}
              </p>
            )}
            <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
              <QuantityInput
                size="sm"
                value={item.quantity}
                max={Math.min(MAX_QUANTITY, Math.max(item.variant.stock, 1))}
                onChange={(q) => onQuantity(item.key, q)}
                disabled={disabled}
              />
              <div className="text-end">
                {item.discount_percent > 0 && !compact && (
                  <del className="text-muted block text-xs">{formatPrice(item.unit_price * item.quantity, false)}</del>
                )}
                <span className="text-sm font-bold">{formatPrice(item.line_total)}</span>
              </div>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
