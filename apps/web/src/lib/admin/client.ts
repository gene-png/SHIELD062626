"use client";

import type { AdminIntakeQueueResponse } from "./types";

export async function fetchIntakeQueue(): Promise<AdminIntakeQueueResponse> {
  const res = await fetch("/api/proxy/admin/intake-queue", {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load intake queue (${res.status}).`);
  }
  return (await res.json()) as AdminIntakeQueueResponse;
}
