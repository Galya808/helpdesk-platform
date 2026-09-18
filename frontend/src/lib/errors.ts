import { ApiError } from "@/lib/api";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.responseBody;
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
    return `Request failed (${error.status})`;
  }
  return error instanceof Error ? error.message : "Unexpected error";
}
