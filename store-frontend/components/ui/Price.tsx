import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

import { Badge } from "./Badge";

type Props = {
  basePrice: number;
  finalPrice: number;
  discountPercent: number;
  size?: "sm" | "md" | "lg";
  showBadge?: boolean;
  className?: string;
};

/** Final price + struck-through base price when discounted. Display only — never sent to the server. */
export function Price({ basePrice, finalPrice, discountPercent, size = "md", showBadge = false, className }: Props) {
  const discounted = discountPercent > 0 && finalPrice < basePrice;
  return (
    <div className={cn("flex flex-wrap items-center gap-x-2 gap-y-1", className)}>
      <span className={cn("text-ink font-bold", size === "sm" && "text-sm", size === "md" && "text-base", size === "lg" && "text-2xl")}>
        {formatPrice(finalPrice)}
      </span>
      {discounted && (
        <>
          <del className={cn("text-muted", size === "lg" ? "text-base" : "text-xs")} aria-label={`قیمت قبل: ${formatPrice(basePrice)}`}>
            {formatPrice(basePrice, false)}
          </del>
          {showBadge && <Badge tone="sale">{formatPercent(discountPercent)}</Badge>}
        </>
      )}
    </div>
  );
}
