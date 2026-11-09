"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { M, ORDER_STATUS_LABELS } from "@/constants/messages";
import { errorMessage } from "@/lib/api/errors";
import { meApi } from "@/lib/api/shop";
import { formatJalaliDate, formatPrice, toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { OrderStatus } from "@/types/api";

import { OrderStatusBadge } from "./OrderStatusBadge";

const FILTERS: (OrderStatus | "")[] = ["", "pending", "paid", "processing", "shipped", "delivered", "cancelled"];

export function OrdersList() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const status = (params.get("status") ?? "") as OrderStatus | "";
  const page = Math.max(1, Number(params.get("page")) || 1);

  const orders = useQuery({
    queryKey: ["orders", status, page],
    queryFn: () => meApi.orders({ page, status: status || undefined }),
  });

  const setParam = (next: Record<string, string>) => {
    const sp = new URLSearchParams(params.toString());
    Object.entries(next).forEach(([k, v]) => (v ? sp.set(k, v) : sp.delete(k)));
    router.push(`${pathname}?${sp.toString()}`);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label={M.account.status}>
        {FILTERS.map((s) => (
          <button
            key={s || "all"}
            role="tab"
            type="button"
            aria-selected={status === s}
            onClick={() => setParam({ status: s, page: "" })}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm whitespace-nowrap",
              status === s ? "bg-ink text-white" : "bg-surface ring-line hover:bg-sand ring-1",
            )}
          >
            {s ? ORDER_STATUS_LABELS[s] : M.account.all}
          </button>
        ))}
      </div>

      {orders.isLoading && <Skeleton className="h-48" />}
      {orders.isError && <p className="text-sale text-sm">{errorMessage(orders.error)}</p>}
      {orders.data && orders.data.results.length === 0 && (
        <EmptyState title={M.account.noOrders} action={<ButtonLink href="/">{M.cart.continue}</ButtonLink>} />
      )}

      {orders.data && orders.data.results.length > 0 && (
        <ul className="flex flex-col gap-3">
          {orders.data.results.map((order) => (
            <li key={order.id}>
              <Link
                href={`/account/orders/${order.id}`}
                className="rounded-card bg-surface ring-line hover:ring-ink flex flex-wrap items-center justify-between gap-3 p-5 ring-1"
              >
                <div className="flex flex-col gap-1">
                  <span className="ltr-nums text-end font-bold">{toFaDigits(order.number)}</span>
                  <span className="text-muted text-xs">{formatJalaliDate(order.created_at)}</span>
                </div>
                <OrderStatusBadge status={order.status} />
                <span className="text-muted text-sm">
                  {toFaDigits(order.items.reduce((s, i) => s + (i.quantity ?? 0), 0))} {M.account.items}
                </span>
                <span className="font-bold">{formatPrice(order.total)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {orders.data && (orders.data.next || orders.data.previous) && (
        <div className="flex justify-center gap-2">
          <button
            type="button"
            disabled={!orders.data.previous}
            onClick={() => setParam({ page: String(page - 1) })}
            className="ring-line rounded-lg px-4 py-2 text-sm ring-1 disabled:opacity-40"
          >
            {M.common.previous}
          </button>
          <button
            type="button"
            disabled={!orders.data.next}
            onClick={() => setParam({ page: String(page + 1) })}
            className="ring-line rounded-lg px-4 py-2 text-sm ring-1 disabled:opacity-40"
          >
            {M.common.next}
          </button>
        </div>
      )}
    </div>
  );
}
