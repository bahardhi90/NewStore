import type { ReactNode } from "react";

import { M } from "@/constants/messages";
import { formatPrice } from "@/lib/format";

type Props = {
  subtotal: number;
  discountTotal: number;
  total: number;
  shippingCost?: number | null;
  children?: ReactNode;
  note?: string;
};

export function CartSummary({ subtotal, discountTotal, total, shippingCost, children, note }: Props) {
  const payable = total + (shippingCost ?? 0);
  return (
    <div className="rounded-card bg-surface ring-line flex flex-col gap-3 p-5 ring-1">
      <dl className="flex flex-col gap-3 text-sm">
        <div className="flex justify-between">
          <dt className="text-muted">{M.cart.subtotal}</dt>
          <dd>{formatPrice(subtotal)}</dd>
        </div>
        {discountTotal > 0 && (
          <div className="text-sale flex justify-between">
            <dt>{M.cart.discount}</dt>
            <dd>{formatPrice(discountTotal)}</dd>
          </div>
        )}
        {shippingCost !== undefined && shippingCost !== null && (
          <div className="flex justify-between">
            <dt className="text-muted">{M.checkout.shippingCost}</dt>
            <dd>{shippingCost === 0 ? M.checkout.free : formatPrice(shippingCost)}</dd>
          </div>
        )}
        <div className="border-line flex justify-between border-t pt-3 text-base font-bold">
          <dt>{M.cart.total}</dt>
          <dd>{formatPrice(payable)}</dd>
        </div>
      </dl>
      {note && <p className="text-muted text-xs">{note}</p>}
      {children}
    </div>
  );
}
