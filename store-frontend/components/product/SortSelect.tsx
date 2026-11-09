"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { M } from "@/constants/messages";

const OPTIONS = Object.entries(M.listing.sortOptions) as [string, string][];

export function SortSelect() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const value = params.get("ordering") ?? "newest";

  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-muted">{M.listing.sort}:</span>
      <select
        value={value}
        onChange={(e) => {
          const next = new URLSearchParams(params.toString());
          if (e.target.value === "newest") next.delete("ordering");
          else next.set("ordering", e.target.value);
          next.delete("page");
          const q = next.toString();
          router.push(q ? `${pathname}?${q}` : pathname, { scroll: false });
        }}
        className="border-line bg-surface focus:border-ink h-10 rounded-lg border px-3 focus:outline-none"
      >
        {OPTIONS.map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}
