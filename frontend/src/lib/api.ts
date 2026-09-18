import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly responseBody: unknown,
  ) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const headers = new Headers(options.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${env.apiUrl}${normalizedPath}`, {
    ...options,
    headers,
  });

  const responseBody: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, responseBody);
  }

  return responseBody as T;
}
