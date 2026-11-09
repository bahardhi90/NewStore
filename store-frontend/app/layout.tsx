import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { Providers } from "@/components/layout/Providers";
import { M } from "@/constants/messages";
import { getSiteSettings } from "@/lib/api/catalog";
import { SITE_URL } from "@/lib/env";

import "./globals.css";

const vazirmatn = localFont({
  src: "./fonts/Vazirmatn-wght.woff2",
  variable: "--font-vazirmatn",
  weight: "100 900",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const site = await getSiteSettings();
  return {
    metadataBase: new URL(SITE_URL),
    title: { default: `${site.brand_name} | ${M.siteKind}`, template: `%s | ${site.brand_name}` },
    description: site.tagline,
    openGraph: { type: "website", locale: "fa_IR", siteName: site.brand_name },
    alternates: { canonical: "/" },
  };
}

export const viewport: Viewport = {
  themeColor: "#fbfaf8",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl" className={vazirmatn.variable}>
      <body className="flex min-h-dvh flex-col">
        <a
          href="#main"
          className="focus:bg-ink sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:px-4 focus:py-2 focus:text-white"
        >
          پرش به محتوای اصلی
        </a>
        <Providers>
          <Header />
          <main id="main" className="flex-1">
            {children}
          </main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
