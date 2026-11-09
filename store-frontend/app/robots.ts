import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/env";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/account", "/checkout", "/cart", "/login", "/payment", "/api/"] }],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
