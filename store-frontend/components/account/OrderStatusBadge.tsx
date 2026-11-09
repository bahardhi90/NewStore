import { Badge } from "@/components/ui/Badge";
import { ORDER_STATUS_LABELS } from "@/constants/messages";
import type { OrderStatus } from "@/types/api";

const TONES: Record<OrderStatus, "warning" | "success" | "brand" | "neutral" | "sale"> = {
  pending: "warning",
  paid: "success",
  processing: "brand",
  shipped: "brand",
  delivered: "success",
  cancelled: "neutral",
  refunded: "neutral",
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <Badge tone={TONES[status]}>{ORDER_STATUS_LABELS[status]}</Badge>;
}
