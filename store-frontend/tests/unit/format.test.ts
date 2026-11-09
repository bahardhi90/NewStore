import { describe, expect, it } from "vitest";

import { formatCountdown, formatPercent, formatPrice, normalizePhone, toEnDigits, toFaDigits } from "@/lib/format";

describe("format", () => {
  it("formats Toman with Persian digits", () => {
    expect(formatPrice(1250000)).toBe("۱٬۲۵۰٬۰۰۰ تومان");
    expect(formatPrice(1250000, false)).toBe("۱٬۲۵۰٬۰۰۰");
  });

  it("converts digits both ways", () => {
    expect(toFaDigits("1405-000123")).toBe("۱۴۰۵-۰۰۰۱۲۳");
    expect(toEnDigits("۰۹۱۲٣٤٥")).toBe("0912345");
  });

  it("normalizes Iranian phone numbers", () => {
    expect(normalizePhone("۰۹۱۲۱۲۳۴۵۶۷")).toBe("09121234567");
    expect(normalizePhone("+989121234567")).toBe("09121234567");
    expect(normalizePhone("9121234567")).toBe("09121234567");
  });

  it("formats percent and countdown", () => {
    expect(formatPercent(20)).toBe("۲۰٪");
    expect(formatCountdown(95)).toBe("۰۱:۳۵");
  });
});
