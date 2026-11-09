import type { Metadata } from "next";

import { ClockIcon, MapPinIcon, PhoneIcon } from "@/components/ui/icons";
import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import { getStores } from "@/lib/api/catalog";
import { emptyDuringBuild } from "@/lib/env";
import { toFaDigits } from "@/lib/format";

export const revalidate = 300;
export const metadata: Metadata = { title: M.stores.title, alternates: { canonical: "/stores" } };

export default async function StoresPage() {
  const stores = await getStores().catch(emptyDuringBuild([]));
  const cities = [...new Set(stores.map((s) => s.city))];

  return (
    <div className="container-page flex flex-col gap-8 py-8">
      <header>
        <h1 className="text-2xl font-black sm:text-3xl">{M.stores.title}</h1>
        <p className="text-muted mt-2">{M.stores.subtitle}</p>
      </header>
      {cities.map((city) => (
        <section key={city} aria-labelledby={`city-${city}`}>
          <h2 id={`city-${city}`} className="mb-4 text-lg font-bold">
            {city}
          </h2>
          <ul className="grid gap-4 md:grid-cols-2">
            {stores
              .filter((s) => s.city === city)
              .map((store) => (
                <li key={store.id} className="rounded-card bg-surface ring-line flex flex-col overflow-hidden ring-1">
                  {store.image && (
                    <div className="relative aspect-[16/7]">
                      <SmartImage src={store.image} alt={store.name} fill sizes="50vw" className="object-cover" />
                    </div>
                  )}
                  <div className="flex flex-col gap-3 p-5 text-sm">
                    <p className="text-base font-bold">{store.name}</p>
                    <p className="text-ink-soft flex gap-2 leading-7">
                      <MapPinIcon className="mt-1 size-4 shrink-0" />
                      {store.address}
                    </p>
                    {store.hours && (
                      <p className="text-ink-soft flex items-center gap-2">
                        <ClockIcon className="size-4 shrink-0" />
                        {store.hours}
                      </p>
                    )}
                    {store.phone && (
                      <a href={`tel:${store.phone.replace(/\D/g, "")}`} className="text-ink-soft hover:text-ink flex items-center gap-2">
                        <PhoneIcon className="size-4 shrink-0" />
                        <span className="ltr-nums">{toFaDigits(store.phone)}</span>
                      </a>
                    )}
                    {store.latitude != null && store.longitude != null && (
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${store.latitude},${store.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="border-line hover:border-ink mt-1 w-fit rounded-lg border px-3 py-2 text-xs"
                      >
                        {M.stores.map}
                      </a>
                    )}
                  </div>
                </li>
              ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
