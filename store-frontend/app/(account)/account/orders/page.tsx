import { Suspense } from "react";

import { OrdersList } from "@/components/account/OrdersList";
import { Skeleton } from "@/components/ui/Skeleton";
import { M } from "@/constants/messages";

export default function OrdersPage() {
  return (
    <section className="flex flex-col gap-5">
      <h1 className="text-xl font-black">{M.account.orders}</h1>
      <Suspense fallback={<Skeleton className="h-64" />}>
        <OrdersList />
      </Suspense>
    </section>
  );
}
