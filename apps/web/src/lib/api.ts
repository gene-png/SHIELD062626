/**
 * Server-side fetch helper for the FastAPI backend.
 *
 * Always runs on the server (don't import from a "use client" file). The
 * client never talks directly to the API - calls flow through this module
 * inside Server Components / Server Actions / route handlers. That keeps
 * the API host name and the Bearer token off the wire to the browser.
 */

const BASE_URL = process.env.API_BASE_URL ?? "http://api:8000";

type Json = Record<string, unknown> | unknown[];

export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: Json;
  bearer?: string;
  headers?: Record<string, string>;
  cache?: RequestCache;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly correlationId: string | undefined,
    public readonly payload: unknown,
  ) {
    super(`API ${status}`);
  }
}

export async function apiFetch<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts.headers ?? {}),
  };
  if (opts.bearer) {
    headers.Authorization = `Bearer ${opts.bearer}`;
  }
  let body: BodyInit | undefined;
  if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body,
    cache: opts.cache ?? "no-store",
  });
  const correlationId = res.headers.get("X-Request-ID") ?? undefined;
  if (!res.ok) {
    let payload: unknown = undefined;
    try {
      payload = await res.json();
    } catch {
      payload = await res.text();
    }
    throw new ApiError(res.status, correlationId, payload);
  }
  // 204 No Content: don't try to JSON-parse.
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}
