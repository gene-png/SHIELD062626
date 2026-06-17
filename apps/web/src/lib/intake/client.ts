"use client";

import type {
  EngagementCreateRequest,
  EngagementResponse,
  IntakePatchRequest,
  IntakeStateResponse,
  IntakeSubmitRequest,
} from "./types";

/**
 * Client-side wrappers that call the same-origin proxy routes. The proxy
 * (apps/web/src/app/api/proxy/intake/...) attaches the user's bearer
 * token server-side, keeping the API host name and the access token off
 * the wire to the browser.
 */

class ProxyError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: unknown,
  ) {
    super(`Intake proxy ${status}`);
  }
}

export async function fetchIntake(): Promise<IntakeStateResponse> {
  const res = await fetch("/api/proxy/intake", { cache: "no-store" });
  if (!res.ok) {
    throw new ProxyError(res.status, await safeJson(res));
  }
  return (await res.json()) as IntakeStateResponse;
}

export async function patchIntake(
  body: IntakePatchRequest,
): Promise<IntakeStateResponse> {
  const res = await fetch("/api/proxy/intake", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ProxyError(res.status, await safeJson(res));
  }
  return (await res.json()) as IntakeStateResponse;
}

export async function submitIntake(
  body: IntakeSubmitRequest,
): Promise<IntakeStateResponse> {
  const res = await fetch("/api/proxy/intake/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ProxyError(res.status, await safeJson(res));
  }
  return (await res.json()) as IntakeStateResponse;
}

export async function fetchEngagements(): Promise<EngagementResponse[]> {
  const res = await fetch("/api/proxy/intake/engagements", {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ProxyError(res.status, await safeJson(res));
  }
  return (await res.json()) as EngagementResponse[];
}

export async function createEngagement(
  body: EngagementCreateRequest,
): Promise<EngagementResponse> {
  const res = await fetch("/api/proxy/intake/engagements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ProxyError(res.status, await safeJson(res));
  }
  return (await res.json()) as EngagementResponse;
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return await res.text();
  }
}

export { ProxyError };
