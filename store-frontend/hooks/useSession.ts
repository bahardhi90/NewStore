"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { AUTH_EXPIRED_EVENT } from "@/lib/api/client";
import { isApiError } from "@/lib/api/errors";
import { meApi } from "@/lib/api/shop";
import type { User } from "@/types/api";

export const SESSION_KEY = ["session"] as const;

/** Current user (null for guests). Backed by GET /me/ through the cookie BFF. */
export function useSession() {
  const queryClient = useQueryClient();
  const query = useQuery<User | null>({
    queryKey: SESSION_KEY,
    queryFn: async () => {
      try {
        return await meApi.get();
      } catch (error) {
        if (isApiError(error) && error.status === 401) return null;
        throw error;
      }
    },
    staleTime: 5 * 60_000,
    retry: false,
  });

  useEffect(() => {
    const onExpired = () => queryClient.setQueryData(SESSION_KEY, null);
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, [queryClient]);

  return { user: query.data ?? null, isLoading: query.isLoading, isLoggedIn: !!query.data };
}
