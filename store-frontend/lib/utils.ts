import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Build a query string from a plain object, skipping empty values. */
export function toQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Next.js searchParams -> single string values */
export function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function isSvg(src: string | null | undefined): boolean {
  return !!src && /\.svg($|\?)/i.test(src);
}

/** Animated GIFs would lose their animation if converted by the image optimizer. */
export function isGif(src: string | null | undefined): boolean {
  return !!src && /\.gif($|\?)/i.test(src);
}
