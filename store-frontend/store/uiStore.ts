"use client";

import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";
export type Toast = { id: number; kind: ToastKind; message: string };

type UiState = {
  miniCartOpen: boolean;
  navDrawerOpen: boolean;
  toasts: Toast[];
  openMiniCart: () => void;
  closeMiniCart: () => void;
  setNavDrawer: (open: boolean) => void;
  toast: (message: string, kind?: ToastKind) => void;
  dismissToast: (id: number) => void;
};

let toastId = 0;

export const useUi = create<UiState>()((set, get) => ({
  miniCartOpen: false,
  navDrawerOpen: false,
  toasts: [],
  openMiniCart: () => set({ miniCartOpen: true }),
  closeMiniCart: () => set({ miniCartOpen: false }),
  setNavDrawer: (open) => set({ navDrawerOpen: open }),
  toast: (message, kind = "info") => {
    toastId += 1;
    const id = toastId;
    set({ toasts: [...get().toasts.slice(-3), { id, kind, message }] });
    setTimeout(() => get().dismissToast(id), kind === "error" ? 6000 : 3500);
  },
  dismissToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}));

/** Shortcut usable outside React components. */
export const toast = {
  success: (message: string) => useUi.getState().toast(message, "success"),
  error: (message: string) => useUi.getState().toast(message, "error"),
  info: (message: string) => useUi.getState().toast(message, "info"),
};
