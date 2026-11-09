"use client";

import { ButtonLink } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { M } from "@/constants/messages";
import { useCart } from "@/hooks/useCart";
import { formatPrice } from "@/lib/format";
import { useUi } from "@/store/uiStore";

import { CartLines } from "./CartLines";

export function MiniCart() {
  const open = useUi((s) => s.miniCartOpen);
  const close = useUi((s) => s.closeMiniCart);
  const { cart, setQuantity, remove, isMutating } = useCart();

  return (
    <Modal open={open} onClose={close} title={M.cart.title} variant="side">
      {cart.items.length === 0 ? (
        <div className="flex flex-col items-center gap-4 p-10 text-center">
          <p className="text-muted">{M.cart.empty}</p>
          <ButtonLink href="/" variant="outline" onClick={close}>
            {M.cart.continue}
          </ButtonLink>
        </div>
      ) : (
        <div className="flex h-full flex-col">
          <div className="flex-1 px-5">
            <CartLines items={cart.items} onQuantity={setQuantity} onRemove={remove} disabled={isMutating} compact />
          </div>
          <div className="border-line bg-surface sticky bottom-0 flex flex-col gap-3 border-t p-5">
            <div className="flex justify-between text-sm font-bold">
              <span>{M.cart.total}</span>
              <span>{formatPrice(cart.total)}</span>
            </div>
            <ButtonLink href="/cart" onClick={close} className="w-full">
              {M.cart.viewCart}
            </ButtonLink>
          </div>
        </div>
      )}
    </Modal>
  );
}
