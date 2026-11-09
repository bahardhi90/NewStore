import type { Metadata } from "next";
import { Suspense } from "react";

import { PaymentResult } from "@/components/checkout/PaymentResult";
import { Skeleton } from "@/components/ui/Skeleton";

export const metadata: Metadata = { title: "نتیجه پرداخت", robots: { index: false } };

export default function PaymentResultPage() {
  return (
    <div className="container-page flex justify-center py-12">
      <Suspense fallback={<Skeleton className="h-72 w-full max-w-lg" />}>
        <PaymentResult />
      </Suspense>
    </div>
  );
}
