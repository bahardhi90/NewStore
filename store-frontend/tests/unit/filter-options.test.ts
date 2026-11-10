import { describe, expect, it } from "vitest";

import { uniqueFilterOptions } from "@/lib/filter-options";

describe("uniqueFilterOptions", () => {
  it("lists each size and color once, keeping the order", () => {
    const result = uniqueFilterOptions({
      sizes: ["S", "S", "M", "S", "L", "M"],
      colors: [
        { name: "مشکی", hex: "#000" },
        { name: "سفید", hex: "#fff" },
        { name: "مشکی", hex: "#111" },
      ],
      min_price: 1,
      max_price: 2,
    });
    expect(result.sizes).toEqual(["S", "M", "L"]);
    expect(result.colors).toEqual([
      { name: "مشکی", hex: "#000" },
      { name: "سفید", hex: "#fff" },
    ]);
    expect(result.min_price).toBe(1);
  });
});
