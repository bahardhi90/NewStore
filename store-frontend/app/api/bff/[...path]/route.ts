/**
 * Backend-for-frontend proxy: the browser calls /api/bff/<path>, this handler forwards to
 * the Django API with the JWT taken from the httpOnly cookie. Tokens never reach JavaScript.
 * On 401 it refreshes the token once (rotation) and retries.
 */
import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE, clearAuthCookies, setAuthCookies } from "@/lib/server/auth-cookies";
import { backendFetch, clientIp } from "@/lib/server/backend";

const ALLOWED_PREFIXES = [
  "cart/",
  "orders/",
  "payments/",
  "me/",
  "shipping-methods/",
  "products/",
  "categories/",
  "collections/",
  "home/",
  "stores/",
];

async function handle(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const joined = `${path.map(encodeURIComponent).join("/")}/`;
  if (!ALLOWED_PREFIXES.some((prefix) => joined.startsWith(prefix))) {
    return NextResponse.json({ detail: "یافت نشد.", code: "not_found", errors: {} }, { status: 404 });
  }

  const jar = await cookies();
  let access = jar.get(ACCESS_COOKIE)?.value ?? null;
  const refresh = jar.get(REFRESH_COOKIE)?.value ?? null;

  let body: unknown = undefined;
  if (request.method !== "GET" && request.method !== "DELETE") {
    try {
      body = await request.json();
    } catch {
      body = {};
    }
  }
  const search = request.nextUrl.searchParams;
  const apiPath = `/${joined}`;
  const ip = clientIp(request);

  let refreshed: { access: string; refresh: string } | null = null;
  if (!access && refresh) {
    refreshed = await tryRefresh(refresh, ip);
    access = refreshed?.access ?? null;
  }

  let result = await backendFetch(apiPath, { method: request.method, body, token: access, search, clientIp: ip });

  if (result.status === 401 && refresh && !refreshed) {
    refreshed = await tryRefresh(refresh, ip);
    if (refreshed) {
      result = await backendFetch(apiPath, { method: request.method, body, token: refreshed.access, search, clientIp: ip });
    }
  }

  const response =
    result.status === 204 ? new NextResponse(null, { status: 204 }) : NextResponse.json(result.data, { status: result.status });
  if (refreshed) setAuthCookies(response, refreshed);
  else if (result.status === 401 && (access || refresh)) clearAuthCookies(response);
  response.headers.set("Cache-Control", "no-store");
  return response;
}

async function tryRefresh(refresh: string, ip: string | null): Promise<{ access: string; refresh: string } | null> {
  const result = await backendFetch("/auth/token/refresh/", { method: "POST", body: { refresh }, clientIp: ip });
  if (result.status !== 200) return null;
  const data = result.data as { access: string; refresh?: string };
  return { access: data.access, refresh: data.refresh ?? refresh };
}

export { handle as GET, handle as POST, handle as PATCH, handle as DELETE };
