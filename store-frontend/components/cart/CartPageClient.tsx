"use client";

import { Button, ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { AlertIcon, CartIcon } from "@/components/ui/icons";
import { Skeleton } from "@/components/ui/Skeleton";
import { M } from "@/constants/messages";
import { useCart } from "@/hooks/useCart";
import { useSession } from "@/hooks/useSession";
import { useRouter } from "next/navigation";

import { CartLines } from "./CartLines";
import { CartSummary } from "./CartSummary";

export function CartPageClient() {
  const router = useRouter();
  const { cart, setQuantity, remove, isLoading, isMutating } = useCart();
  const { isLoggedIn } = useSession();

  if (isLoading) {
    return (
      <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (cart.items.length === 0) {
    return (
      <EmptyState
        icon={<CartIcon className="size-10" />}
        title={M.cart.empty}
        text={M.cart.emptyHint}
        action={<ButtonLink href="/">{M.cart.continue}</ButtonLink>}
      />
    );
  }

  const hasProblems = cart.items.some((i) => i.warning);

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[1fr_22rem]">
      <section aria-label={M.cart.title} className="rounded-card bg-surface ring-line px-5 ring-1">
        {cart.warnings.length > 0 && (
          <ul className="bg-warning-soft text-warning mt-4 flex flex-col gap-1 rounded-lg p-3 text-sm">
            {cart.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        )}
        <CartLines items={cart.items} onQuantity={setQuantity} onRemove={remove} disabled={isMutating} />
      </section>
      <div className="lg:sticky lg:top-32">
        <CartSummary subtotal={cart.subtotal} discountTotal={cart.discount_total} total={cart.total} note={M.cart.shippingNote}>
          {hasProblems && (
            <p className="text-warning flex items-start gap-2 text-xs">
              <AlertIcon className="mt-0.5 size-4 shrink-0" />
              {M.cart.hasProblems}
            </p>
          )}
          <Button
            size="lg"
            className="w-full"
            disabled={hasProblems}
            onClick={() => router.push(isLoggedIn ? "/checkout" : "/login?next=/checkout")}
          >
            {M.cart.checkout}
          </Button>
          {!isLoggedIn && <p className="text-muted text-center text-xs">{M.cart.loginToCheckout}</p>}
        </CartSummary>
      </div>
    </div>
  );
}
