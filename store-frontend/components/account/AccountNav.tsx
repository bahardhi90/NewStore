"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { M } from "@/constants/messages";
import { SESSION_KEY, useSession } from "@/hooks/useSession";
import { authApi } from "@/lib/api/shop";
import { toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import { toast } from "@/store/uiStore";

const LINKS = [
  { href: "/account", label: M.account.profile },
  { href: "/account/orders", label: M.account.orders },
  { href: "/account/addresses", label: M.account.addresses },
];

export function AccountNav() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useSession();

  async function logout() {
    await authApi.logout().catch(() => undefined);
    queryClient.setQueryData(SESSION_KEY, null);
    queryClient.removeQueries({ queryKey: ["cart"] });
    toast.info(M.auth.loggedOut);
    router.replace("/");
    router.refresh();
  }

  return (
    <aside className="rounded-card bg-surface ring-line p-4 ring-1">
      {user && (
        <div className="border-line mb-4 border-b px-2 pb-4">
          <p className="font-bold">{[user.first_name, user.last_name].filter(Boolean).join(" ") || M.account.title}</p>
          <p className="ltr-nums text-muted text-end text-sm">{toFaDigits(user.phone)}</p>
        </div>
      )}
      <nav className="flex gap-1 overflow-x-auto lg:flex-col">
        {LINKS.map((link) => {
          const active = link.href === "/account" ? pathname === "/account" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              aria-current={active ? "page" : undefined}
              className={cn("rounded-lg px-3 py-2.5 text-sm whitespace-nowrap", active ? "bg-ink text-white" : "hover:bg-sand")}
            >
              {link.label}
            </Link>
          );
        })}
        <button
          type="button"
          onClick={logout}
          className="text-sale hover:bg-sale-soft rounded-lg px-3 py-2.5 text-start text-sm whitespace-nowrap"
        >
          {M.auth.logout}
        </button>
      </nav>
    </aside>
  );
}
