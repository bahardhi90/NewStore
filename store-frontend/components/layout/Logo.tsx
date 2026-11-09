import Link from "next/link";

import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import type { SiteSettings } from "@/types/api";

/** The uploaded logo, or the site name until one is set in admin. */
export function Logo({ site }: { site: SiteSettings }) {
  const label = `${site.brand_name} | ${M.siteKind}`;
  if (site.logo) {
    return (
      <Link href="/" className="relative block h-10 w-28 shrink-0 sm:w-36" aria-label={label}>
        <SmartImage src={site.logo} alt={site.brand_name} fill sizes="144px" priority className="object-contain object-right" />
      </Link>
    );
  }
  return (
    <Link href="/" className="text-xl font-black tracking-tight" aria-label={label}>
      {site.brand_name}
    </Link>
  );
}
