import type { ProductListItem } from "@/types/api";

import { ProductCard } from "./ProductCard";

export function ProductGrid({ products, priorityCount = 0 }: { products: ProductListItem[]; priorityCount?: number }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-8 md:grid-cols-3 lg:grid-cols-4">
      {products.map((product, i) => (
        <ProductCard key={product.id} product={product} priority={i < priorityCount} />
      ))}
    </div>
  );
}
