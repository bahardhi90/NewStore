"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { CartSummary } from "@/components/cart/CartSummary";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import { errorMessage } from "@/lib/api/errors";
import { checkoutApi, meApi } from "@/lib/api/shop";
import { formatJalaliDate, formatPrice, toFaDigits } from "@/lib/format";
import { toast } from "@/store/uiStore";

import { OrderStatusBadge } from "./OrderStatusBadge";

export function OrderDetail({ id }: { id: number }) {
  const order = useQuery({ queryKey: ["order", id], queryFn: () => meApi.order(id), enabled: Number.isFinite(id) });
  const pay = useMutation({
    mutationFn: () => checkoutApi.startPayment(id),
    onSuccess: ({ redirect_url }) => window.location.assign(redirect_url),
    onError: (error) => toast.error(errorMessage(error)),
  });

  if (order.isLoading) return <Skeleton className="h-96" />;
  if (order.isError || !order.data) return <EmptyState title={M.errors.notFoundTitle} text={errorMessage(order.error)} />;

  const o = order.data;
  const address = o.address;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-black">
          {M.account.orderDetails} <span className="ltr-nums">{toFaDigits(o.number)}</span>
        </h1>
        <OrderStatusBadge status={o.status} />
      </div>

      <div className="rounded-card bg-surface ring-line grid gap-4 p-5 text-sm ring-1 sm:grid-cols-2">
        <p>
          <span className="text-muted">{M.account.date}: </span>
          {formatJalaliDate(o.created_at, true)}
        </p>
        {o.paid_at && (
          <p>
            <span className="text-muted">{M.payment.success}: </span>
            {formatJalaliDate(o.paid_at, true)}
          </p>
        )}
        {o.shipping_method && (
          <p>
            <span className="text-muted">{M.checkout.steps[1]}: </span>
            {o.shipping_method.title}
          </p>
        )}
        {o.tracking_code && (
          <p>
            <span className="text-muted">{M.account.tracking}: </span>
            <span className="ltr-nums">{toFaDigits(o.tracking_code)}</span>
          </p>
        )}
        {address && (
          <p className="sm:col-span-2">
            <span className="text-muted">{M.checkout.steps[0]}: </span>
            {address.province}، {address.city}، {address.address_line} — {address.receiver_name}
          </p>
        )}
      </div>

      <ul className="divide-line rounded-card bg-surface ring-line divide-y px-5 ring-1">
        {o.items.map((item) => (
          <li key={item.id} className="flex gap-4 py-4">
            <div className="bg-sand relative aspect-[4/5] w-16 shrink-0 overflow-hidden rounded-lg">
              <SmartImage src={item.image} alt={item.title ?? ""} fill sizes="64px" className="object-cover" />
            </div>
            <div className="flex flex-1 flex-col gap-1 text-sm">
              {item.product_slug ? (
                <Link href={`/product/${item.product_slug}`} className="font-medium hover:underline">
                  {item.title}
                </Link>
              ) : (
                <span className="font-medium">{item.title}</span>
              )}
              <span className="text-muted text-xs">
                {M.product.size}: {item.size} | {M.product.color}: {item.color} | {M.product.quantity}: {toFaDigits(item.quantity ?? 0)}
              </span>
            </div>
            <span className="text-sm font-bold">{formatPrice(item.line_total ?? 0)}</span>
          </li>
        ))}
      </ul>

      <div className="max-w-sm">
        <CartSummary
          subtotal={o.subtotal}
          discountTotal={o.discount_total}
          total={o.total - o.shipping_cost}
          shippingCost={o.shipping_cost}
        >
          {o.status === "pending" && (
            <Button onClick={() => pay.mutate()} loading={pay.isPending} className="w-full">
              {M.account.payNow}
            </Button>
          )}
        </CartSummary>
      </div>
    </div>
  );
}
