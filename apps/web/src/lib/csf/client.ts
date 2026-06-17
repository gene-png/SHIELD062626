"use client";

import type {
  CsfAnswer,
  CsfAnswerPatch,
  CsfAssessment,
  CsfCatalog,
  CsfDeliverable,
  CsfInterviewQuestionnaire,
  CsfScoreSummary,
  GapAnalysis,
} from "./types";

interface JsonRequestInit {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
}

async function jsonRequest<T>(
  url: string,
  init: JsonRequestInit = {},
): Promise<T> {
  const { body, method = "GET" } = init;
  const res = await fetch(url, {
    method,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let payload: unknown;
    try {
      payload = await res.json();
    } catch {
      payload = await res.text();
    }
    throw new CsfProxyError(res.status, payload);
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}

export class CsfProxyError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: unknown,
  ) {
    super(`CSF proxy ${status}`);
  }
}

export async function fetchCatalog(): Promise<CsfCatalog> {
  return jsonRequest<CsfCatalog>("/api/proxy/csf/catalog");
}

export async function fetchLatestAssessment(
  serviceId: string,
): Promise<CsfAssessment | null> {
  try {
    return await jsonRequest<CsfAssessment>(
      `/api/proxy/csf/services/${serviceId}/assessments/latest`,
    );
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function createAssessment(
  serviceId: string,
): Promise<CsfAssessment> {
  return jsonRequest<CsfAssessment>(
    `/api/proxy/csf/services/${serviceId}/assessments`,
    { method: "POST" },
  );
}

export async function patchAnswer(
  answerId: string,
  patch: CsfAnswerPatch,
): Promise<CsfAnswer> {
  return jsonRequest<CsfAnswer>(`/api/proxy/csf/answers/${answerId}`, {
    method: "PATCH",
    body: patch,
  });
}

export async function fetchInterviewQuestionnaire(
  serviceId: string,
): Promise<CsfInterviewQuestionnaire | null> {
  try {
    return await jsonRequest<CsfInterviewQuestionnaire>(
      `/api/proxy/csf/services/${serviceId}/questionnaire`,
    );
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

// --- Client self-assessment (the client fills + submits their own draft) ---

export async function fetchSelfAssessment(
  serviceId: string,
): Promise<CsfAssessment | null> {
  try {
    return await jsonRequest<CsfAssessment>(
      `/api/proxy/csf/services/${serviceId}/self-assessment`,
    );
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function patchSelfAssessmentAnswer(
  answerId: string,
  patch: CsfAnswerPatch,
): Promise<CsfAnswer> {
  return jsonRequest<CsfAnswer>(
    `/api/proxy/csf/self-assessment/answers/${answerId}`,
    { method: "PATCH", body: patch },
  );
}

export async function submitSelfAssessment(
  serviceId: string,
  body: { target_tier?: number },
): Promise<CsfAssessment> {
  return jsonRequest<CsfAssessment>(
    `/api/proxy/csf/services/${serviceId}/self-assessment/submit`,
    { method: "POST", body },
  );
}

export async function approveAssessment(
  assessmentId: string,
): Promise<CsfAssessment> {
  return jsonRequest<CsfAssessment>(
    `/api/proxy/csf/assessments/${assessmentId}/approve`,
    { method: "POST" },
  );
}

export async function fetchScore(
  serviceId: string,
): Promise<CsfScoreSummary | null> {
  try {
    return await jsonRequest<CsfScoreSummary>(
      `/api/proxy/csf/services/${serviceId}/score`,
    );
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function fetchLatestDeliverable(
  serviceId: string,
): Promise<CsfDeliverable | null> {
  try {
    return await jsonRequest<CsfDeliverable>(
      `/api/proxy/csf/services/${serviceId}/deliverables/latest`,
    );
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function finalizeCsfDeliverable(
  serviceId: string,
): Promise<CsfDeliverable> {
  return jsonRequest<CsfDeliverable>(
    `/api/proxy/csf/services/${serviceId}/deliverables/finalize`,
    { method: "POST" },
  );
}

export async function releaseCsfDeliverable(
  deliverableId: string,
): Promise<CsfDeliverable> {
  return jsonRequest<CsfDeliverable>(
    `/api/proxy/csf/deliverables/${deliverableId}/release`,
    { method: "POST" },
  );
}

export async function fetchGapAnalysis(
  serviceId: string,
  opts: { targetTier?: number; topN?: number } = {},
): Promise<GapAnalysis | null> {
  const params = new URLSearchParams();
  if (opts.targetTier !== undefined) {
    params.set("target_tier", String(opts.targetTier));
  }
  if (opts.topN !== undefined) {
    params.set("top_n", String(opts.topN));
  }
  const qs = params.toString();
  const url = `/api/proxy/csf/services/${serviceId}/gap-analysis${
    qs ? `?${qs}` : ""
  }`;
  try {
    return await jsonRequest<GapAnalysis>(url);
  } catch (err) {
    if (err instanceof CsfProxyError && err.status === 404) {
      return null;
    }
    throw err;
  }
}
