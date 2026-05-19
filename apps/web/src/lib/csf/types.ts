/** Wire types mirroring apps/api/app/schemas/csf.py. */

export type CsfAssessmentStatus = "draft" | "approved" | "released";

export interface CatalogSubcategory {
  code: string;
  function: string;
  category: string;
  name: string;
  outcome: string;
}

export interface CatalogCategory {
  code: string;
  function: string;
  name: string;
  purpose: string;
  subcategories: CatalogSubcategory[];
}

export interface CatalogFunction {
  code: string;
  name: string;
  purpose: string;
  categories: CatalogCategory[];
}

export interface CatalogTier {
  tier: number;
  short_label: string;
  description: string;
}

export interface CsfCatalog {
  functions: CatalogFunction[];
  tiers: CatalogTier[];
  total_subcategories: number;
}

export interface CsfAnswer {
  id: string;
  assessment_id: string;
  subcategory_code: string;
  maturity_tier: number | null;
  notes: string | null;
  evidence_artifact_id: string | null;
  answered_by: string | null;
  answered_at: string | null;
}

export interface CsfAssessment {
  id: string;
  service_id: string;
  version: number;
  status: CsfAssessmentStatus;
  approved_at: string | null;
  approved_by: string | null;
  answers: CsfAnswer[];
}

export interface CsfAnswerPatch {
  maturity_tier?: number | null;
  notes?: string;
  evidence_artifact_id?: string | null;
}

export interface FunctionScore {
  function: string;
  function_name: string;
  subcategory_count: number;
  answered_count: number;
  average_tier: number | null;
  coverage_pct: number;
  weakest_subcategory_codes: string[];
}

export interface CsfScoreSummary {
  assessment_id: string;
  version: number;
  total_subcategories: number;
  answered_subcategories: number;
  coverage_pct: number;
  average_tier: number | null;
  overall_maturity_label: string;
  by_function: FunctionScore[];
}

export interface GapItem {
  code: string;
  function: string;
  function_name: string;
  category: string;
  name: string;
  outcome: string;
  current_tier: number;
  target_tier: number;
  gap_size: number;
  priority_score: number;
  notes: string | null;
}

export interface GapAnalysis {
  assessment_id: string;
  version: number;
  target_tier: number;
  target_label: string;
  total_gap_count: number;
  unscored_count: number;
  gap_count_by_function: Record<string, number>;
  gaps: GapItem[];
}
