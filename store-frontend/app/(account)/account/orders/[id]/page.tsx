import { OrderDetail } from "@/components/account/OrderDetail";

export default async function OrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <OrderDetail id={Number(id)} />;
}
