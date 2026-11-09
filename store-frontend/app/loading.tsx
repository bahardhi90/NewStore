import { ProductGridSkeleton, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="container-page flex flex-col gap-6 py-8" aria-busy="true" aria-label="در حال بارگذاری">
      <Skeleton className="h-6 w-48" />
      <ProductGridSkeleton count={8} />
    </div>
  );
}
