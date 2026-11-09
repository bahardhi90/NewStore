import Link from "next/link";

import { InstagramIcon, TelegramIcon } from "@/components/ui/icons";
import { M } from "@/constants/messages";
import { getSiteSettings, getStores } from "@/lib/api/catalog";
import { toFaDigits } from "@/lib/format";
import type { Store } from "@/types/api";

import { TrustBadges } from "./TrustBadges";

async function loadStores(): Promise<Store[]> {
  try {
    return await getStores();
  } catch {
    return [];
  }
}

const isExternal = (url: string) => /^https?:\/\//.test(url);

export async function Footer() {
  const [allStores, site] = await Promise.all([loadStores(), getSiteSettings()]);
  const stores = allStores.slice(0, 3);
  const year = new Intl.DateTimeFormat("fa-IR-u-ca-persian", { year: "numeric" }).format(new Date());
  const socials = [
    { url: site.instagram_url, label: "اینستاگرام", Icon: InstagramIcon },
    { url: site.telegram_url, label: "تلگرام", Icon: TelegramIcon },
  ].filter((s) => s.url);

  return (
    <footer className="bg-fabric mt-20">
      <div className="container-page py-10">
        <TrustBadges compact />
      </div>
      <div className="container-page border-line grid gap-10 border-t py-10 md:grid-cols-4">
        <div className="flex flex-col gap-3">
          <p className="text-xl font-black">{site.brand_name}</p>
          <p className="text-muted text-sm leading-7">{site.tagline}</p>
          {socials.length > 0 && (
            <div className="flex gap-2">
              {socials.map(({ url, label, Icon }) => (
                <a
                  key={label}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="hover:bg-sand rounded-full p-2"
                >
                  <Icon className="size-5" />
                </a>
              ))}
            </div>
          )}
        </div>
        {site.footer_columns.map((column, i) => (
          <div key={i}>
            <p className="mb-3 text-sm font-bold">{column.title}</p>
            <ul className="text-ink-soft flex flex-col gap-2 text-sm">
              {column.links.map((link, j) => (
                <li key={j}>
                  {isExternal(link.url) ? (
                    <a href={link.url} target="_blank" rel="noopener noreferrer" className="hover:text-ink">
                      {link.title}
                    </a>
                  ) : (
                    <Link href={link.url} className="hover:text-ink">
                      {link.title}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
        {stores.length > 0 && (
          <div>
            <p className="mb-3 text-sm font-bold">{M.stores.title}</p>
            <ul className="text-ink-soft flex flex-col gap-3 text-sm">
              {stores.map((store) => (
                <li key={store.id}>
                  <p className="text-ink font-medium">{store.name}</p>
                  <p className="leading-6">{store.address}</p>
                  {store.phone && <p className="ltr-nums text-end">{toFaDigits(store.phone)}</p>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <div className="border-line text-muted border-t py-5 text-center text-xs">
        © {year} {site.brand_name} — تمامی حقوق محفوظ است.
      </div>
    </footer>
  );
}
