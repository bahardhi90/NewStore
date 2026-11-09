"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import { M } from "@/constants/messages";
import { isApiError } from "@/lib/api/errors";
import { cartApi } from "@/lib/api/shop";
import { useGuestCart, type GuestCartLine } from "@/store/cartStore";
import { toast } from "@/store/uiStore";
import type { Cart, Variant } from "@/types/api";

import { useSession } from "./useSession";

export const CART_KEY = ["cart"] as const;

/** Unified line used by the UI for both guest and server carts. */
export type CartLineView = {
  key: number; // server item id, or variant id for guests
  product: { id: number; title: string; slug: string; image: string | null };
  variant: Variant;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  final_unit_price: number;
  line_total: number;
  warning: string | null;
};

export type CartView = {
  items: CartLineView[];
  item_count: number;
  subtotal: number;
  discount_total: number;
  total: number;
  warnings: string[];
};

const EMPTY: CartView = { items: [], item_count: 0, subtotal: 0, discount_total: 0, total: 0, warnings: [] };

function fromServer(cart: Cart): CartView {
  return {
    items: cart.items.map((i) => ({
      key: i.id,
      product: { id: i.product.id ?? 0, title: i.product.title ?? "", slug: i.product.slug ?? "", image: i.product.image ?? null },
      variant: i.variant,
      quantity: i.quantity,
      unit_price: i.unit_price,
      discount_percent: i.discount_percent ?? 0,
      final_unit_price: i.final_unit_price,
      line_total: i.line_total,
      warning: i.warning ?? null,
    })),
    item_count: cart.item_count,
    subtotal: cart.subtotal,
    discount_total: cart.discount_total,
    total: cart.total,
    warnings: cart.warnings ?? [],
  };
}

function fromGuest(lines: GuestCartLine[]): CartView {
  const items = lines.map<CartLineView>((l) => ({
    key: l.variant.id,
    product: l.product,
    variant: l.variant,
    quantity: l.quantity,
    unit_price: l.base_price,
    discount_percent: l.discount_percent,
    final_unit_price: l.final_price,
    line_total: l.final_price * l.quantity,
    warning: null,
  }));
  const subtotal = items.reduce((sum, i) => sum + i.unit_price * i.quantity, 0);
  const total = items.reduce((sum, i) => sum + i.line_total, 0);
  return {
    items,
    item_count: items.reduce((sum, i) => sum + i.quantity, 0),
    subtotal,
    discount_total: subtotal - total,
    total,
    warnings: [],
  };
}

function showError(error: unknown) {
  if (isApiError(error)) toast.error(error.allMessages()[0]);
  else toast.error(M.errors.generic);
}

/**
 * Guests: Zustand store persisted in localStorage.
 * Logged in: server cart (React Query); every mutation returns the full cart.
 */
export function useCart() {
  const { isLoggedIn, isLoading: sessionLoading } = useSession();
  const queryClient = useQueryClient();
  const guest = useGuestCart();

  const serverCart = useQuery({ queryKey: CART_KEY, queryFn: cartApi.get, enabled: isLoggedIn });

  const setCart = (cart: Cart) => queryClient.setQueryData(CART_KEY, cart);

  const addMutation = useMutation({
    mutationFn: cartApi.add,
    onSuccess: setCart,
    onError: showError,
  });
  const updateMutation = useMutation({
    mutationFn: ({ key, quantity }: { key: number; quantity: number }) => cartApi.update(key, quantity),
    onSuccess: setCart,
    onError: showError,
  });
  const removeMutation = useMutation({
    mutationFn: (key: number) => cartApi.remove(key),
    onSuccess: setCart,
    onError: showError,
  });

  const view = useMemo<CartView>(() => {
    if (isLoggedIn) return serverCart.data ? fromServer(serverCart.data) : EMPTY;
    return fromGuest(guest.lines);
  }, [isLoggedIn, serverCart.data, guest.lines]);

  async function add(line: GuestCartLine): Promise<boolean> {
    if (isLoggedIn) {
      try {
        await addMutation.mutateAsync({ variant_id: line.variant.id, quantity: line.quantity });
        return true;
      } catch {
        return false;
      }
    }
    const existing = guest.lines.find((l) => l.variant.id === line.variant.id)?.quantity ?? 0;
    if (existing + line.quantity > line.variant.stock) {
      toast.error(line.variant.stock === 0 ? M.product.outOfStock : M.product.onlyLeft(String(line.variant.stock)));
      return false;
    }
    guest.add(line);
    return true;
  }

  function setQuantity(key: number, quantity: number) {
    if (isLoggedIn) updateMutation.mutate({ key, quantity });
    else {
      const line = guest.lines.find((l) => l.variant.id === key);
      if (line && quantity > line.variant.stock) {
        toast.error(M.product.onlyLeft(String(line.variant.stock)));
        return;
      }
      guest.setQuantity(key, quantity);
    }
  }

  function remove(key: number) {
    if (isLoggedIn) removeMutation.mutate(key);
    else guest.remove(key);
  }

  return {
    cart: view,
    isServer: isLoggedIn,
    isLoading: sessionLoading || (isLoggedIn && serverCart.isLoading),
    isMutating: addMutation.isPending || updateMutation.isPending || removeMutation.isPending,
    add,
    setQuantity,
    remove,
  };
}
