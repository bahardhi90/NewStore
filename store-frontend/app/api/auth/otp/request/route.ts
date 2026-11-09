import { NextResponse, type NextRequest } from "next/server";

import { backendFetch, clientIp } from "@/lib/server/backend";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const result = await backendFetch("/auth/otp/request/", { method: "POST", body, clientIp: clientIp(request) });
  return NextResponse.json(result.data, { status: result.status });
}
