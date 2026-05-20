/** Wire types mirroring apps/api/app/schemas/zt.py. */

export type ZtFramework = "cisa_ztmm_2_0" | "dod_ztra";
export type ZtAssessmentStatus = "draft" | "approved" | "released";

export interface CatalogCapability {
  code: string;
  pillar_code: string;
  name: string;
  outcome: string;
}

export interface CatalogPillar {
  code: string;
  name: string;
  purpose: string;
  capabilities: CatalogCapability[];
}

export interface CatalogStage {
  stage: number;
  label: string;
  description: string;
}

export interface ZtCatalog {
  framework: ZtFramework;
  pillars: CatalogPillar[];
  stages: CatalogStage[];
  total_capabilities: number;
}

export interface ZtAnswer {
  id: string;
  assessment_id: string;
  capability_code: string;
  maturity_stage: number | null;
  notes: string | null;
  evidence_artifact_id: string | null;
  answered_by: string | null;
  answered_at: string | null;
}

export interface ZtAssessment {
  id: string;
  service_id: string;
  framework: ZtFramework;
  version: number;
  status: ZtAssessmentStatus;
  approved_at: string | null;
  approved_by: string | null;
  answers: ZtAnswer[];
}

export interface ZtAnswerPatch {
  maturity_stage?: number | null;
  notes?: string;
  evidence_artifact_id?: string | null;
}

export interface PillarScore {
  pillar_code: string;
  pillar_name: string;
  capability_count: number;
  answered_count: number;
  average_stage: number | null;
  coverage_pct: number;
  weakest_capability_codes: string[];
}

export interface ZtScoreSummary {
  assessment_id: string;
  version: number;
  framework: ZtFramework;
  total_capabilities: number;
  answered_capabilities: number;
  coverage_pct: number;
  average_stage: number | null;
  overall_stage_label: string;
  by_pillar: PillarScore[];
}

export interface GapItem {
  code: string;
  pillar_code: string;
  pillar_name: string;
  name: string;
  outcome: string;
  current_stage: number;
  target_stage: number;
  gap_size: number;
  priority_score: number;
  notes: string | null;
}

export interface GapAnalysis {
  assessment_id: string;
  version: number;
  framework: ZtFramework;
  target_stage: number;
  target_label: string;
  total_gap_count: number;
  unscored_count: number;
  gap_count_by_pillar: Record<string, number>;
  gaps: GapItem[];
}
