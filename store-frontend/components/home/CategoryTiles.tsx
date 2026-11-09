import Link from "next/link";

import { SmartImage } from "@/components/ui/SmartImage";
import type { Category } from "@/types/api";

export function CategoryTiles({ categories }: { categories: Category[] }) {
  return (
    <ul className="grid grid-cols-3 gap-3 sm:gap-5">
      {categories.map((category) => (
        <li key={category.id}>
          <Link href={`/category/${category.slug}`} className="group rounded-card bg-sand relative block aspect-square overflow-hidden">
            <SmartImage
              src={category.image}
              alt=""
              fill
              sizes="33vw"
              className="object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <span className="absolute inset-0 flex items-end bg-gradient-to-t from-black/50 to-transparent p-3 text-sm font-bold text-white sm:p-5 sm:text-xl">
              {category.name}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
