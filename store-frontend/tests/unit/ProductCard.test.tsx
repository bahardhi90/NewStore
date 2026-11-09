import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProductCard } from "@/components/product/ProductCard";

const product = {
  id: 1,
  title: "کت پشمی کلاسیک",
  slug: "classic-wool-jacket",
  image: "/mock/jacket-black.svg",
  hover_image: "/mock/jacket-navy.svg",
  base_price: 4500000,
  discount_percent: 20,
  final_price: 3600000,
};

describe("<ProductCard />", () => {
  it("renders title, link, discount badge and prices", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByRole("heading", { name: product.title })).toBeInTheDocument();
    expect(screen.getAllByRole("link")[0]).toHaveAttribute("href", "/product/classic-wool-jacket");
    expect(screen.getByText("۲۰٪")).toBeInTheDocument();
    expect(screen.getByText("۳٬۶۰۰٬۰۰۰ تومان")).toBeInTheDocument();
  });

  it("hides the badge when there is no discount", () => {
    render(<ProductCard product={{ ...product, discount_percent: 0, final_price: product.base_price }} />);
    expect(screen.queryByText("۲۰٪")).not.toBeInTheDocument();
  });
});
