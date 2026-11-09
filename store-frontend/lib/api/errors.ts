import { M } from "@/constants/messages";
import type { ApiErrorBody } from "@/types/api";

/** Normalized API error ({detail, code, errors}) usable everywhere on the client. */
export class ApiError extends Error {
  status: number;
  code: string;
  errors: Record<string, string[]>;

  constructor(status: number, body: Partial<ApiErrorBody> | null | undefined) {
    super(body?.detail || M.errors.generic);
    this.name = "ApiError";
    this.status = status;
    this.code = body?.code || "error";
    this.errors = body?.errors ?? {};
  }

  /** First message for a field (for forms). */
  field(name: string): string | undefined {
    return this.errors[name]?.[0];
  }

  /** All messages in one list (used for toasts). */
  allMessages(): string[] {
    const list = Object.entries(this.errors)
      .filter(([key]) => key !== "retry_after")
      .flatMap(([, messages]) => messages);
    return list.length ? list : [this.message];
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function errorMessage(error: unknown): string {
  if (isApiError(error)) return error.message;
  return M.errors.generic;
}
