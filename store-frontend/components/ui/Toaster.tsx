"use client";

import { useUi } from "@/store/uiStore";
import { cn } from "@/lib/utils";

import { AlertIcon, CheckIcon, CloseIcon } from "./icons";

export function Toaster() {
  const toasts = useUi((s) => s.toasts);
  const dismiss = useUi((s) => s.dismissToast);
  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4"
      aria-live="polite"
      role="status"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "animate-fade-in pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-lg px-4 py-3 text-sm shadow-lg",
            t.kind === "error" && "bg-sale text-white",
            t.kind === "success" && "bg-ink text-white",
            t.kind === "info" && "bg-surface text-ink ring-line ring-1",
          )}
        >
          {t.kind === "error" ? <AlertIcon className="mt-0.5 size-4 shrink-0" /> : <CheckIcon className="mt-0.5 size-4 shrink-0" />}
          <p className="flex-1 leading-6">{t.message}</p>
          <button type="button" onClick={() => dismiss(t.id)} aria-label="بستن" className="opacity-70 hover:opacity-100">
            <CloseIcon className="size-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
