"use client";

import Link from "next/link";

import { CartIcon, UserIcon } from "@/components/ui/icons";
import { M } from "@/constants/messages";
import { useCart } from "@/hooks/useCart";
import { useSession } from "@/hooks/useSession";
import { toFaDigits } from "@/lib/format";
import { useUi } from "@/store/uiStore";

export function HeaderActions() {
  const { cart } = useCart();
  const { user } = useSession();
  const openMiniCart = useUi((s) => s.openMiniCart);
  const count = cart.item_count;

  return (
    <div className="ms-auto flex items-center gap-1 md:ms-0">
      <Link
        href={user ? "/account" : "/login"}
        className="hover:bg-sand flex h-10 items-center gap-2 rounded-full px-3 text-sm"
        aria-label={user ? M.nav.account : M.nav.login}
      >
        <UserIcon className="size-5" />
        <span className="hidden xl:inline">{user ? user.first_name || M.nav.account : M.nav.login}</span>
      </Link>
      <button
        type="button"
        onClick={openMiniCart}
        className="hover:bg-sand relative flex size-10 items-center justify-center rounded-full"
        aria-label={`${M.nav.cart} (${toFaDigits(count)})`}
      >
        <CartIcon className="size-5" />
        {count > 0 && (
          <span className="bg-sale absolute -end-0.5 -top-0.5 flex min-w-5 items-center justify-center rounded-full px-1 text-[11px] font-bold text-white">
            {toFaDigits(count)}
          </span>
        )}
      </button>
    </div>
  );
}
