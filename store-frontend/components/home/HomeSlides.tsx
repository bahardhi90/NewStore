import Link from "next/link";
import type { ReactNode } from "react";

import { SmartImage } from "@/components/ui/SmartImage";
import type { Banner, Collection } from "@/types/api";

import { SectionHeader } from "./SectionHeader";

/** Full-screen picture or silent looping video. The whole slide is the link: no separate button. */
function MediaSlide({
  image,
  imageMobile,
  video,
  alt,
  title,
  text,
  href,
  priority = false,
}: {
  image: string | null | undefined;
  imageMobile?: string | null;
  video?: string | null;
  alt: string;
  title?: string | null;
  text?: string | null;
  href?: string | null;
  priority?: boolean;
}) {
  const content = (
    <>
      {video ? (
        <video
          src={video}
          poster={image ?? undefined}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          aria-hidden="true"
          className="absolute inset-0 size-full object-cover"
        />
      ) : (
        <>
          {imageMobile && (
            <SmartImage src={imageMobile} alt={alt} fill priority={priority} sizes="100vw" className="object-cover sm:hidden" />
          )}
          <SmartImage
            src={image}
            alt={alt}
            fill
            priority={priority}
            sizes="100vw"
            className={imageMobile ? "object-cover max-sm:hidden" : "object-cover"}
          />
        </>
      )}
      {(title || text) && (
        <>
          <div className="absolute inset-0 bg-gradient-to-l from-black/50 via-black/10 to-transparent" />
          <div className="container-page absolute inset-0 flex flex-col justify-center gap-4 text-white">
            {title && <h2 className="max-w-xl text-3xl leading-tight font-black sm:text-5xl">{title}</h2>}
            {text && <p className="max-w-lg text-base opacity-90 sm:text-lg">{text}</p>}
          </div>
        </>
      )}
    </>
  );

  return href ? (
    <Link href={href} className="bg-sand relative block h-full" aria-label={title || alt || undefined}>
      {content}
    </Link>
  ) : (
    <div className="bg-sand relative h-full">{content}</div>
  );
}

export function BannerSlide({ banner, priority }: { banner: Banner; priority: boolean }) {
  return (
    <MediaSlide
      image={banner.image}
      imageMobile={banner.image_mobile}
      video={banner.video}
      alt={banner.title ?? ""}
      title={banner.title}
      text={banner.subtitle}
      href={banner.link}
      priority={priority}
    />
  );
}

export function CollectionSlide({ collection }: { collection: Collection }) {
  return (
    <MediaSlide
      image={collection.banner}
      alt={collection.title}
      title={collection.title}
      text={collection.description}
      href={`/collection/${collection.slug}`}
    />
  );
}

export function SectionSlide({ title, href, children }: { title: string; href?: string; children: ReactNode }) {
  return (
    <div className="container-page flex h-full flex-col justify-center py-6">
      <SectionHeader title={title} href={href} />
      {children}
    </div>
  );
}
