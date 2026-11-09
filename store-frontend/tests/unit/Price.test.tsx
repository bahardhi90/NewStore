import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Price } from "@/components/ui/Price";

describe("<Price />", () => {
  it("shows struck-through base price and badge when discounted", () => {
    render(<Price basePrice={2000000} finalPrice={1600000} discountPercent={20} showBadge />);
    expect(screen.getByText("۱٬۶۰۰٬۰۰۰ تومان")).toBeInTheDocument();
    expect(screen.getByText("۲٬۰۰۰٬۰۰۰").tagName).toBe("DEL");
    expect(screen.getByText("۲۰٪")).toBeInTheDocument();
  });

  it("shows only the final price without discount", () => {
    render(<Price basePrice={1000000} finalPrice={1000000} discountPercent={0} />);
    expect(screen.getByText("۱٬۰۰۰٬۰۰۰ تومان")).toBeInTheDocument();
    expect(document.querySelector("del")).toBeNull();
  });
});
