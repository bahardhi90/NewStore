import { NextResponse, type NextRequest } from "next/server";

/**
 * Route protection (Next.js 16 "proxy", formerly middleware).
 * Only checks that a refresh cookie exists; the real validation happens in the backend.
 */
export function proxy(request: NextRequest) {
  const hasSession = Boolean(request.cookies.get("refresh_token")?.value);
  const { pathname, search } = request.nextUrl;

  if (!hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/account/:path*", "/checkout/:path*"],
};
