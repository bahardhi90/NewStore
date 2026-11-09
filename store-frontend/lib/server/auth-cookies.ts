import "server-only";

import type { NextResponse } from "next/server";

import { IS_PROD } from "@/lib/env";

export const ACCESS_COOKIE = "access_token";
export const REFRESH_COOKIE = "refresh_token";

const ACCESS_MAX_AGE = 60 * 14; // slightly shorter than the 15 min backend lifetime
const REFRESH_MAX_AGE = 60 * 60 * 24 * 7;

const base = { httpOnly: true, secure: IS_PROD, sameSite: "lax" as const, path: "/" };

export function setAuthCookies(response: NextResponse, tokens: { access: string; refresh: string }): void {
  response.cookies.set(ACCESS_COOKIE, tokens.access, { ...base, maxAge: ACCESS_MAX_AGE });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...base, maxAge: REFRESH_MAX_AGE });
}

export function clearAuthCookies(response: NextResponse): void {
  response.cookies.set(ACCESS_COOKIE, "", { ...base, maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...base, maxAge: 0 });
}
