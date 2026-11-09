import { describe, expect, it } from "vitest";

import { calcFinalPrice } from "@/lib/mocks/data";
import { addressSchema, otpCodeSchema, phoneSchema } from "@/lib/validation";

describe("validation", () => {
  it("accepts Persian digits in phone and code", () => {
    expect(phoneSchema.parse("۰۹۱۲۱۲۳۴۵۶۷")).toBe("09121234567");
    expect(otpCodeSchema.parse("۱۲۳۴۵")).toBe("12345");
    expect(phoneSchema.safeParse("0812").success).toBe(false);
  });

  it("validates addresses", () => {
    const ok = addressSchema.safeParse({
      title: "خانه",
      receiver_name: "علی",
      receiver_phone: "09121234567",
      province: "تهران",
      city: "تهران",
      postal_code: "۱۲۳۴۵-۶۷۸۹۰",
      address_line: "ولیعصر",
      is_default: false,
    });
    expect(ok.success).toBe(true);
    expect(ok.success && ok.data.postal_code).toBe("1234567890");
  });
});

describe("price formula (same as backend)", () => {
  it("rounds down to 1,000 Toman", () => {
    expect(calcFinalPrice(1234567, 10)).toBe(1111000);
    expect(calcFinalPrice(1000000, 0)).toBe(1000000);
  });
});
