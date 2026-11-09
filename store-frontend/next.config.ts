import type { NextConfig } from "next";

/** Media host of the Django backend (images come from /media/ or S3). */
function mediaPatterns() {
  const urls = [process.env.NEXT_PUBLIC_API_URL, process.env.NEXT_PUBLIC_MEDIA_URL].filter(Boolean) as string[];
  const patterns = urls.map((raw) => {
    const url = new URL(raw);
    return {
      protocol: url.protocol.replace(":", "") as "http" | "https",
      hostname: url.hostname,
      port: url.port,
      pathname: "/**",
    };
  });
  patterns.push({ protocol: "http", hostname: "localhost", port: "8000", pathname: "/**" });
  return patterns;
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  images: {
    remotePatterns: mediaPatterns(),
    qualities: [75, 90],
    formats: ["image/avif", "image/webp"],
    // Allows optimizing images served from localhost/private IPs (dev, or ALLOW_LOCAL_IMAGES=true for local prod tests).
    dangerouslyAllowLocalIP: process.env.NODE_ENV !== "production" || process.env.ALLOW_LOCAL_IMAGES === "true",
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
