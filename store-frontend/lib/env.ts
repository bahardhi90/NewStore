export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");

/** Server-side API base URL (can be an internal Docker hostname). */
export function serverApiUrl(): string {
  return (process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
}

export const IS_PROD = process.env.NODE_ENV === "production";

/**
 * For pages pre-rendered at build time: the backend may not be running yet (e.g. a fresh server),
 * so render them empty instead of failing the build; ISR refreshes them with real data soon after.
 * At runtime the error is re-thrown, so Next keeps serving the last good version.
 */
export function emptyDuringBuild<T>(fallback: T) {
  return (error: unknown): T => {
    if (process.env.NEXT_PHASE === "phase-production-build") return fallback;
    throw error;
  };
}
