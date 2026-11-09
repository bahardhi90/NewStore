import Link from "next/link";

import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import type { Collection } from "@/types/api";

export function CollectionBanner({ collection, asLink = true }: { collection: Collection; asLink?: boolean }) {
  const content = (
    <div className="rounded-card bg-sand relative aspect-[16/9] overflow-hidden sm:aspect-[16/5]">
      <SmartImage src={collection.banner} alt={collection.title} fill sizes="100vw" className="object-cover" priority={!asLink} />
      <div className="absolute inset-0 flex flex-col justify-center gap-2 bg-gradient-to-l from-black/40 to-transparent p-6 text-white sm:p-12">
        <h2 className="text-2xl font-black sm:text-4xl">{collection.title}</h2>
        {collection.description && <p className="max-w-md text-sm opacity-90 sm:text-base">{collection.description}</p>}
        {asLink && <span className="text-ink mt-2 w-fit rounded-lg bg-white px-5 py-2.5 text-sm font-bold">{M.home.viewAll}</span>}
      </div>
    </div>
  );
  return asLink ? <Link href={`/collection/${collection.slug}`}>{content}</Link> : content;
}
