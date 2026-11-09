import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AccountNav } from "@/components/account/AccountNav";
import { M } from "@/constants/messages";

export const metadata: Metadata = { title: M.account.title, robots: { index: false } };

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <div className="container-page grid items-start gap-8 py-8 lg:grid-cols-[16rem_1fr]">
      <AccountNav />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
