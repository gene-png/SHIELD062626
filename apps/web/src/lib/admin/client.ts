"use client";

import type {
  AdminIntakeQueueResponse,
  FulfillServiceRequestResponse,
} from "./types";

export async function fetchIntakeQueue(): Promise<AdminIntakeQueueResponse> {
  const res = await fetch("/api/proxy/admin/intake-queue", {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load intake queue (${res.status}).`);
  }
  return (await res.json()) as AdminIntakeQueueResponse;
}

export async function fulfillServiceRequest(
  requestId: string,
): Promise<FulfillServiceRequestResponse> {
  const res = await fetch(
    `/api/proxy/admin/service-requests/${requestId}/fulfill`,
    { method: "POST" },
  );
  if (!res.ok) {
    let detail = `Failed to publish (${res.status}).`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return (await res.json()) as FulfillServiceRequestResponse;
}
