import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type Tone = "sale" | "neutral" | "success" | "warning" | "brand";

const tones: Record<Tone, string> = {
  sale: "bg-sale text-white",
  neutral: "bg-sand text-ink-soft",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  brand: "bg-brand-soft text-brand",
};

export function Badge({ tone = "neutral", className, children }: { tone?: Tone; className?: string; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold", tones[tone], className)}>{children}</span>
  );
}
