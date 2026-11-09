import Link from "next/link";

import { M } from "@/constants/messages";

export function SectionHeader({ title, href }: { title: string; href?: string }) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <h2 className="text-xl font-black sm:text-2xl">{title}</h2>
      {href && (
        <Link href={href} className="text-ink-soft hover:text-ink text-sm underline-offset-4 hover:underline">
          {M.home.viewAll}
        </Link>
      )}
    </div>
  );
}
