"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { Variant } from "@/types/api";

/** A guest-cart line. Prices are a display snapshot only; the server recalculates on checkout. */
export type GuestCartLine = {
  variant: Variant;
  product: { id: number; title: string; slug: string; image: string | null };
  quantity: number;
  base_price: number;
  discount_percent: number;
  final_price: number;
};

type GuestCartState = {
  lines: GuestCartLine[];
  add: (line: GuestCartLine) => void;
  setQuantity: (variantId: number, quantity: number) => void;
  remove: (variantId: number) => void;
  clear: () => void;
};

export const MAX_QUANTITY = 10;

export const useGuestCart = create<GuestCartState>()(
  persist(
    (set) => ({
      lines: [],
      add: (line) =>
        set((state) => {
          const existing = state.lines.find((l) => l.variant.id === line.variant.id);
          if (existing) {
            return {
              lines: state.lines.map((l) =>
                l.variant.id === line.variant.id
                  ? { ...line, quantity: Math.min(l.quantity + line.quantity, MAX_QUANTITY, line.variant.stock) }
                  : l,
              ),
            };
          }
          return { lines: [...state.lines, { ...line, quantity: Math.min(line.quantity, MAX_QUANTITY, line.variant.stock) }] };
        }),
      setQuantity: (variantId, quantity) =>
        set((state) => ({
          lines: state.lines.map((l) =>
            l.variant.id === variantId ? { ...l, quantity: Math.max(1, Math.min(quantity, MAX_QUANTITY)) } : l,
          ),
        })),
      remove: (variantId) => set((state) => ({ lines: state.lines.filter((l) => l.variant.id !== variantId) })),
      clear: () => set({ lines: [] }),
    }),
    {
      name: "store-guest-cart",
      skipHydration: true,
      version: 1,
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
