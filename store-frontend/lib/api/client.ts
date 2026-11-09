import axios, { AxiosError } from "axios";

import { M } from "@/constants/messages";
import type { ApiErrorBody } from "@/types/api";

import { ApiError } from "./errors";

/**
 * Browser HTTP client. All calls go through our own Next.js route handlers (/api/...),
 * which attach the JWT from the httpOnly cookie and refresh it when needed.
 */
export const http = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: { Accept: "application/json" },
  timeout: 20_000,
});

export const AUTH_EXPIRED_EVENT = "store:auth-expired";

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (!error.response) {
      return Promise.reject(new ApiError(0, { detail: M.errors.network, code: "network_error", errors: {} }));
    }
    const { status, data } = error.response;
    if (status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
    return Promise.reject(new ApiError(status, data));
  },
);

/** "/me/orders/" -> "/bff/me/orders" (Next.js routes have no trailing slash; the BFF adds it for Django). */
const toBff = (path: string) => `/bff${path.replace(/\/+$/, "")}`;

/** Calls go to /api/bff/<backend path> */
export const bff = {
  get: async <T>(path: string, params?: Record<string, unknown>) => (await http.get<T>(toBff(path), { params })).data,
  post: async <T>(path: string, body?: unknown) => (await http.post<T>(toBff(path), body ?? {})).data,
  patch: async <T>(path: string, body?: unknown) => (await http.patch<T>(toBff(path), body ?? {})).data,
  delete: async <T>(path: string) => (await http.delete<T>(toBff(path))).data,
};
