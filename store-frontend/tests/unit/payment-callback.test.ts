import { describe, expect, it } from "vitest";

import { paymentResultPath } from "@/lib/payment-callback";

const query = (path: string) => new URLSearchParams(path.split("?")[1]);

describe("paymentResultPath", () => {
  it("maps a successful Digipay callback", () => {
    const path = paymentResultPath(new URLSearchParams("authority=DP1&result=SUCCESS&trackingCode=TC&type=13&amount=1000"));
    expect(path.startsWith("/payment/result?")).toBe(true);
    const out = query(path);
    expect(out.get("Authority")).toBe("DP1");
    expect(out.get("Status")).toBe("OK");
    expect(out.get("TrackingCode")).toBe("TC");
    expect(out.get("Type")).toBe("13");
    expect(out.has("amount")).toBe(false);
  });

  it("marks a failed Digipay callback", () => {
    expect(query(paymentResultPath(new URLSearchParams("authority=DP1&result=FAILURE"))).get("Status")).toBe("NOK");
  });

  it("reads the SnappPay state field", () => {
    expect(query(paymentResultPath(new URLSearchParams("authority=SP1&state=OK"))).get("Status")).toBe("OK");
    expect(query(paymentResultPath(new URLSearchParams("authority=SP1&state=FAILED"))).get("Status")).toBe("NOK");
  });

  it("falls back to the ids in the body when the query string was dropped", () => {
    expect(query(paymentResultPath(new URLSearchParams("providerId=DP2&result=SUCCESS"))).get("Authority")).toBe("DP2");
    expect(query(paymentResultPath(new URLSearchParams("transactionId=SP2&state=OK"))).get("Authority")).toBe("SP2");
  });

  it("leaves the decision to verification when no outcome was sent", () => {
    expect(query(paymentResultPath(new URLSearchParams("authority=SP1"))).get("Status")).toBe("OK");
  });

  it("shows the invalid-return page without an authority", () => {
    expect(paymentResultPath(new URLSearchParams("state=OK"))).toBe("/payment/result");
  });
});
