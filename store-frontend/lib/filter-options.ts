import type { ProductFilterOptions } from "@/types/api";

/** Never show a size or color twice, even if the API (or an old cached answer) repeats one. */
export function uniqueFilterOptions(options: ProductFilterOptions): ProductFilterOptions {
  const colors = new Map<string | undefined, NonNullable<ProductFilterOptions["colors"]>[number]>();
  for (const color of options.colors ?? []) if (!colors.has(color.name)) colors.set(color.name, color);
  return { ...options, sizes: [...new Set(options.sizes ?? [])], colors: [...colors.values()] };
}
