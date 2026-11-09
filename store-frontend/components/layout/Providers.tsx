"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useEffect, useState, type ReactNode } from "react";

import { Toaster } from "@/components/ui/Toaster";
import { useGuestCart } from "@/store/cartStore";

import { MiniCart } from "../cart/MiniCart";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 },
          mutations: { retry: 0 },
        },
      }),
  );

  // The guest cart lives in localStorage; hydrate after mount to avoid SSR mismatches.
  useEffect(() => {
    void useGuestCart.persist.rehydrate();
  }, []);

  return (
    <QueryClientProvider client={client}>
      {children}
      <MiniCart />
      <Toaster />
      {process.env.NODE_ENV === "development" && <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />}
    </QueryClientProvider>
  );
}
