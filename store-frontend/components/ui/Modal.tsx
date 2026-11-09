"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

import { M } from "@/constants/messages";
import { cn } from "@/lib/utils";

import { CloseIcon } from "./icons";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
  /** "center" dialog or a "side" drawer that slides in from the start (right in RTL). */
  variant?: "center" | "side";
};

/** Accessible dialog based on the native <dialog> element (focus trap + Esc built in). */
export function Modal({ open, onClose, title, children, className, variant = "center" }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
      className={cn(
        "backdrop:animate-fade-in m-0 max-h-none max-w-none bg-transparent p-0 backdrop:bg-black/40",
        variant === "center" && "fixed inset-0 m-auto h-fit w-[min(92vw,36rem)]",
        variant === "side" && "fixed inset-y-0 start-0 h-dvh w-[min(92vw,26rem)]",
      )}
    >
      <div
        className={cn(
          "bg-surface text-ink flex flex-col shadow-xl",
          variant === "center" && "rounded-card animate-fade-in max-h-[85vh]",
          variant === "side" && "animate-slide-in-start h-full",
          className,
        )}
      >
        <div className="border-line flex items-center justify-between border-b px-5 py-4">
          <h2 id={titleId} className="text-base font-bold">
            {title}
          </h2>
          <button type="button" onClick={onClose} className="hover:bg-sand rounded-md p-1.5" aria-label={M.nav.close}>
            <CloseIcon className="size-5" />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </dialog>
  );
}
