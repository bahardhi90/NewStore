import type { Metadata } from "next";

import { CartPageClient } from "@/components/cart/CartPageClient";
import { M } from "@/constants/messages";

export const metadata: Metadata = { title: M.cart.title, robots: { index: false } };

export default function CartPage() {
  return (
    <div className="container-page py-8">
      <h1 className="mb-6 text-2xl font-black">{M.cart.title}</h1>
      <CartPageClient />
    </div>
  );
}
