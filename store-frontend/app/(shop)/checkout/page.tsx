import type { Metadata } from "next";

import { CheckoutClient } from "@/components/checkout/CheckoutClient";
import { M } from "@/constants/messages";

export const metadata: Metadata = { title: M.checkout.title, robots: { index: false } };

export default function CheckoutPage() {
  return (
    <div className="container-page py-8">
      <h1 className="mb-6 text-2xl font-black">{M.checkout.title}</h1>
      <CheckoutClient />
    </div>
  );
}
