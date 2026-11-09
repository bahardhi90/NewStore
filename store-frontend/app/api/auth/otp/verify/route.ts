import { NextResponse, type NextRequest } from "next/server";

import { setAuthCookies } from "@/lib/server/auth-cookies";
import { backendFetch, clientIp } from "@/lib/server/backend";
import type { AuthTokens } from "@/types/api";

/** Verifies the OTP, stores tokens in httpOnly cookies, returns only {user, is_new}. */
export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const result = await backendFetch("/auth/otp/verify/", { method: "POST", body, clientIp: clientIp(request) });
  if (result.status !== 200) return NextResponse.json(result.data, { status: result.status });

  const tokens = result.data as AuthTokens;
  const response = NextResponse.json({ user: tokens.user, is_new: tokens.is_new });
  setAuthCookies(response, tokens);
  return response;
}
