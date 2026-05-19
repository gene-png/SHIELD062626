/**
 * Wire types matching apps/api/app/schemas/intake.py.
 *
 * Kept in app/lib so they're consumable from both Server and Client
 * Components without dragging a separate package import path.
 */

export type ServiceType =
  | "tech_debt"
  | "zero_trust_cisa"
  | "zero_trust_dod"
  | "nist_csf"
  | "attack_coverage"
  | "consultation";

export interface ClientProfileResponse {
  id: string;
  legal_name: string;
  dba_name: string | null;
  website: string | null;
  size_band: string | null;
  industry: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string | null;
  prompting_context: string | null;
  service_interests: string[] | null;
  intake_completed_at: string | null;
}

export interface ServiceRequestResponse {
  id: string;
  service_type: ServiceType;
  requested_by: string;
  requested_at: string;
  notes: string | null;
  deadline: string | null;
  fulfilled_service_id: string | null;
  declined_at: string | null;
  declined_reason: string | null;
}

export interface IntakeStateResponse {
  client: ClientProfileResponse | null;
  service_requests: ServiceRequestResponse[];
  intake_completed_at: string | null;
}

export interface ClientProfilePatch {
  legal_name?: string;
  dba_name?: string;
  website?: string;
  size_band?: string;
  industry?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  prompting_context?: string;
  service_interests?: ServiceType[];
}

export interface IntakePatchRequest {
  client?: ClientProfilePatch;
  display_name?: string;
  title?: string;
  phone?: string;
  timezone?: string;
}

export interface ServiceRequestInput {
  service_type: ServiceType;
  notes?: string;
  deadline?: string;
}

export interface IntakeSubmitRequest {
  client: ClientProfilePatch;
  service_requests: ServiceRequestInput[];
  display_name?: string;
  title?: string;
  phone?: string;
  timezone?: string;
}

export const SERVICE_LABELS: Record<ServiceType, string> = {
  tech_debt: "Technical Debt Review",
  zero_trust_cisa: "Zero Trust Assessment (CISA ZTMM 2.0)",
  zero_trust_dod: "Zero Trust Assessment (DoD ZTRA)",
  nist_csf: "NIST CSF 2.0 Assessment",
  attack_coverage: "MITRE ATT&CK Coverage Mapping",
  consultation: "I'm not sure — start with a consultation",
};

export const WIZARD_STEPS = [
  { key: "services", label: "Services" },
  { key: "organization", label: "Organization" },
  { key: "contact", label: "Contact" },
  { key: "systems", label: "Systems" },
  { key: "notes", label: "Notes & artifacts" },
  { key: "review", label: "Review & submit" },
] as const;

export type WizardStepKey = (typeof WIZARD_STEPS)[number]["key"];
