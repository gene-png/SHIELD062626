/**
 * Wire types mirroring apps/api/app/schemas/admin.py.
 */

import type { ClientProfileResponse, ServiceType } from "@/lib/intake/types";

export interface AdminUserSummary {
  id: string;
  email: string;
  display_name: string | null;
  title: string | null;
  role: "admin" | "reviewer" | "client";
  last_login_at: string | null;
  created_at: string;
}

export interface AdminServiceRequestRow {
  id: string;
  service_type: ServiceType;
  requested_at: string;
  requested_by: AdminUserSummary;
  notes: string | null;
  deadline: string | null;
  csf_target_tier: number | null;
  csf_profile: string | null;
  zt_target_stage: number | null;
  fulfilled_service_id: string | null;
  declined_at: string | null;
  declined_reason: string | null;
}

export interface AdminArtifactRow {
  id: string;
  title: string;
  mime_type: string;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
}

export interface AdminIntakeQueueResponse {
  client: ClientProfileResponse | null;
  intake_completed_at: string | null;
  service_requests: AdminServiceRequestRow[];
  artifacts: AdminArtifactRow[];
  total_users: number;
}
