/**
 * Digipay and SnappPay send the browser back with a POST, which a page can't receive. This maps
 * their fields to the query string of /payment/result. Status is only a hint: the backend asks the
 * gateway directly before an order is marked as paid.
 */
const SUCCESS_VALUES = ["OK", "SUCCESS"];

export function paymentResultPath(params: URLSearchParams): string {
  const authority = params.get("authority") ?? params.get("providerId") ?? params.get("transactionId");
  if (!authority) return "/payment/result";

  // No explicit outcome is treated as OK so a paid order isn't cancelled; verification decides.
  const outcome = (params.get("result") ?? params.get("state") ?? "OK").toUpperCase();
  const query = new URLSearchParams({ Authority: authority, Status: SUCCESS_VALUES.includes(outcome) ? "OK" : "NOK" });

  const trackingCode = params.get("trackingCode");
  const type = params.get("type");
  if (trackingCode) query.set("TrackingCode", trackingCode);
  if (type) query.set("Type", type);
  return `/payment/result?${query.toString()}`;
}
