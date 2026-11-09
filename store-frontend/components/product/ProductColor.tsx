"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

type ProductColorState = { color: string | null; setColor: (color: string) => void };

const ProductColorContext = createContext<ProductColorState>({ color: null, setColor: () => {} });

/** Shares the chosen color between the color buttons and the gallery on the product page. */
export function ProductColorProvider({ initial, children }: { initial: string | null; children: ReactNode }) {
  const [color, setColor] = useState(initial);
  return <ProductColorContext.Provider value={{ color, setColor }}>{children}</ProductColorContext.Provider>;
}

export const useProductColor = () => useContext(ProductColorContext);
