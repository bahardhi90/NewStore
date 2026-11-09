import Link from "next/link";

import { Badge } from "@/components/ui/Badge";
import { Price } from "@/components/ui/Price";
import { SmartImage } from "@/components/ui/SmartImage";
import { formatPercent } from "@/lib/format";
import type { ProductListItem } from "@/types/api";

export function ProductCard({ product, priority = false }: { product: ProductListItem; priority?: boolean }) {
  const discounted = product.discount_percent > 0;
  return (
    <article className="group flex flex-col gap-3">
      <Link
        href={`/product/${product.slug}`}
        className="rounded-card bg-sand relative block aspect-[4/5] overflow-hidden"
        aria-label={product.title}
      >
        <SmartImage
          src={product.image}
          alt={product.title}
          fill
          priority={priority}
          sizes="(min-width: 1024px) 25vw, (min-width: 768px) 33vw, 50vw"
          className="object-cover transition-opacity duration-300 group-hover:opacity-0"
        />
        {product.hover_image && (
          <SmartImage
            src={product.hover_image}
            alt=""
            fill
            sizes="(min-width: 1024px) 25vw, (min-width: 768px) 33vw, 50vw"
            className="object-cover opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          />
        )}
        {discounted && (
          <Badge tone="sale" className="absolute start-3 top-3 text-sm">
            {formatPercent(product.discount_percent)}
          </Badge>
        )}
      </Link>
      <div className="flex flex-col gap-1.5 px-0.5">
        <h3 className="line-clamp-1 text-sm font-medium">
          <Link href={`/product/${product.slug}`} className="hover:underline">
            {product.title}
          </Link>
        </h3>
        <Price basePrice={product.base_price} finalPrice={product.final_price} discountPercent={product.discount_percent} size="sm" />
      </div>
    </article>
  );
}
