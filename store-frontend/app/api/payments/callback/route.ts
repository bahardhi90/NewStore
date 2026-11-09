import type { NextRequest } from "next/server";

import { paymentResultPath } from "@/lib/payment-callback";

async function readBody(request: NextRequest): Promise<Record<string, string>> {
  try {
    if (request.headers.get("content-type")?.includes("application/json")) {
      return Object.fromEntries(Object.entries(await request.json()).map(([key, value]) => [key, String(value)]));
    }
    return Object.fromEntries([...(await request.formData()).entries()].map(([key, value]) => [key, String(value)]));
  } catch {
    return {};
  }
}

async function handle(request: NextRequest) {
  const params = new URLSearchParams(request.nextUrl.searchParams);
  if (request.method === "POST") {
    for (const [key, value] of Object.entries(await readBody(request))) params.set(key, value);
  }
  // A relative Location stays on the public host even behind a proxy. 303 turns the POST into a GET.
  return new Response(null, { status: 303, headers: { Location: paymentResultPath(params) } });
}

export { handle as GET, handle as POST };
