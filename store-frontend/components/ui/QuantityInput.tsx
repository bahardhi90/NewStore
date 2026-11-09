"use client";

import { toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";

import { MinusIcon, PlusIcon } from "./icons";

type Props = {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max: number;
  disabled?: boolean;
  size?: "sm" | "md";
  label?: string;
};

export function QuantityInput({ value, onChange, min = 1, max, disabled, size = "md", label = "تعداد" }: Props) {
  const btn = cn("flex items-center justify-center hover:bg-sand disabled:opacity-30", size === "sm" ? "size-8" : "size-11");
  return (
    <div className="border-line bg-surface inline-flex items-center rounded-lg border" role="group" aria-label={label}>
      <button type="button" className={btn} onClick={() => onChange(value + 1)} disabled={disabled || value >= max} aria-label="افزایش">
        <PlusIcon className="size-4" />
      </button>
      <span className={cn("min-w-8 text-center font-medium", size === "sm" ? "text-sm" : "text-base")} aria-live="polite">
        {toFaDigits(value)}
      </span>
      <button type="button" className={btn} onClick={() => onChange(value - 1)} disabled={disabled || value <= min} aria-label="کاهش">
        <MinusIcon className="size-4" />
      </button>
    </div>
  );
}
