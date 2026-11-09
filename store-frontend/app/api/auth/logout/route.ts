import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE, clearAuthCookies } from "@/lib/server/auth-cookies";
import { backendFetch, clientIp } from "@/lib/server/backend";

export async function POST(request: NextRequest) {
  const jar = await cookies();
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  const access = jar.get(ACCESS_COOKIE)?.value;
  if (refresh) {
    // Best effort: blacklist the refresh token on the backend.
    await backendFetch("/auth/logout/", { method: "POST", body: { refresh }, token: access ?? null, clientIp: clientIp(request) });
  }
  const response = new NextResponse(null, { status: 204 });
  clearAuthCookies(response);
  return response;
}
