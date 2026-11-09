/**
 * Server-only bridge to the Django API (or the in-memory mock when NEXT_PUBLIC_USE_MOCKS=true).
 * Used by Server Components and by the /api/* route handlers (BFF).
 */
import "server-only";

import { serverApiUrl, USE_MOCKS } from "@/lib/env";
import { handleMock } from "@/lib/mocks/router";
import type { ApiErrorBody } from "@/types/api";

export type BackendResult = { status: number; data: unknown };

type BackendOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  search?: URLSearchParams | string;
  /** Next.js data cache revalidate seconds (GET only, ignored for authenticated calls). */
  revalidate?: number | false;
  /** The visitor's IP (see `clientIp()`), so Django's rate limits count each visitor separately. */
  clientIp?: string | null;
};

/** The visitor's IP as set by the reverse proxy (Caddy overwrites any value sent by the browser). */
export function clientIp(request: Request): string | null {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return forwarded || request.headers.get("x-real-ip") || null;
}

/**
 * When API_URL points at Django inside the Docker network (http://web:8000/api), tell Django the
 * public host and scheme so it builds https://api.<domain>/media/... links and skips the HTTPS redirect.
 */
function forwardedHostHeaders(): Record<string, string> {
  const publicUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!process.env.API_URL || !publicUrl) return {};
  const { host, protocol } = new URL(publicUrl);
  return { "X-Forwarded-Host": host, "X-Forwarded-Proto": protocol.replace(":", "") };
}

export async function backendFetch(path: string, options: BackendOptions = {}): Promise<BackendResult> {
  const method = (options.method ?? "GET").toUpperCase();
  const search = typeof options.search === "string" ? new URLSearchParams(options.search) : (options.search ?? new URLSearchParams());

  if (USE_MOCKS) {
    return handleMock(method, path, search, (options.body as Record<string, unknown>) ?? null, options.token ?? null);
  }

  const query = search.toString();
  const url = `${serverApiUrl()}${path}${query ? `?${query}` : ""}`;
  const headers: Record<string, string> = { Accept: "application/json", "Accept-Language": "fa", ...forwardedHostHeaders() };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.clientIp) headers["X-Forwarded-For"] = options.clientIp;

  const cacheable = method === "GET" && !options.token && options.revalidate !== undefined;
  try {
    const response = await fetch(url, {
      method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      ...(cacheable
        ? options.revalidate === false
          ? { cache: "force-cache" as const }
          : { next: { revalidate: options.revalidate } }
        : { cache: "no-store" as const }),
    });
    if (response.status === 204) return { status: 204, data: null };
    const text = await response.text();
    let data: unknown = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: "پاسخ نامعتبر از سرور.", code: "bad_response", errors: {} } satisfies ApiErrorBody;
    }
    return { status: response.status, data };
  } catch {
    return {
      status: 503,
      data: { detail: "ارتباط با سرور برقرار نشد.", code: "network_error", errors: {} } satisfies ApiErrorBody,
    };
  }
}

export class ServerApiError extends Error {
  constructor(
    public status: number,
    public body: ApiErrorBody,
  ) {
    super(body.detail);
  }
}

/** GET for Server Components. Throws ServerApiError on non-2xx. */
export async function serverGet<T>(path: string, search?: URLSearchParams | string, revalidate: number | false = 60): Promise<T> {
  const result = await backendFetch(path, { search, revalidate });
  if (result.status >= 400) {
    const body = (result.data as ApiErrorBody) ?? { detail: "خطا", code: "error", errors: {} };
    throw new ServerApiError(result.status, body);
  }
  return result.data as T;
}
