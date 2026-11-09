import Image, { type ImageProps } from "next/image";

import { isGif, isSvg } from "@/lib/utils";

/** next/image wrapper: SVGs (mock data) and GIFs skip optimization; null src shows a neutral block. */
export function SmartImage({ src, alt, className, ...rest }: Omit<ImageProps, "src"> & { src: string | null | undefined }) {
  if (!src) return <div className={`bg-sand ${className ?? ""}`} role="img" aria-label={alt} />;
  return <Image src={src} alt={alt} className={className} unoptimized={isSvg(src) || isGif(src)} {...rest} />;
}
