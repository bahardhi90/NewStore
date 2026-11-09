import type { ProductDetail } from "@/types/api";

/** The color first selected on the product page: the first one in stock. Used on the server and the client. */
export function initialColor(product: ProductDetail): string | null {
  return (product.variants.find((v) => v.stock > 0) ?? product.variants[0])?.color ?? null;
}
