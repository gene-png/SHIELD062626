import { describe, expect, it } from "vitest";

import {
  CSF_FUNCTION_CODES,
  CSF_TIERS,
  csfLevelGuidance,
  csfTierExplainer,
} from "./csf";
import { ZT_STAGES, ztStageGuidance } from "./zt";

/**
 * S6 completeness pins. Every level a client can pick has to carry both a
 * plain-language explainer and a worked example, so these cases iterate the
 * whole set (6 CSF functions x 4 tiers, CISA 4 stages, DoD 3 stages) instead of
 * sampling. Deleting a single entry turns one of them red, because the lookups
 * throw on a missing key rather than returning a default.
 */

describe("CSF maturity guidance", () => {
  it("carries a plain-language explainer for each of the four tiers", () => {
    expect(CSF_TIERS).toHaveLength(4);
    const explainers = CSF_TIERS.map((tier) => csfTierExplainer(tier));
    for (const [index, text] of explainers.entries()) {
      expect(text, `tier ${CSF_TIERS[index]} explainer`).toMatch(/\S/);
    }
    expect(new Set(explainers).size).toBe(4);
  });

  it("carries a worked example for every function at every tier (6x4)", () => {
    expect(CSF_FUNCTION_CODES).toHaveLength(6);
    const examples: string[] = [];
    for (const code of CSF_FUNCTION_CODES) {
      for (const tier of CSF_TIERS) {
        const guidance = csfLevelGuidance(code, tier);
        expect(guidance.explainer, `${code} T${tier} explainer`).toMatch(/\S/);
        expect(guidance.example, `${code} T${tier} example`).toMatch(/\S/);
        examples.push(guidance.example);
      }
    }
    expect(examples).toHaveLength(24);
    // Distinct text, so a copy-pasted example cannot pass as coverage.
    expect(new Set(examples).size).toBe(24);
  });

  it("refuses an unknown function or tier instead of returning a default", () => {
    expect(() => csfLevelGuidance("XX", 1)).toThrow(/XX/);
    expect(() => csfLevelGuidance("GV", 9)).toThrow(/9/);
    expect(() => csfTierExplainer(0)).toThrow(/0/);
  });

  it("keeps level labels and descriptions out of the guidance module", () => {
    // Labels and full descriptions come from the catalog payload the API builds
    // from TIER_DEFINITIONS, so the module carries no copy that could drift.
    for (const code of CSF_FUNCTION_CODES) {
      for (const tier of CSF_TIERS) {
        expect(Object.keys(csfLevelGuidance(code, tier)).sort()).toEqual([
          "example",
          "explainer",
        ]);
      }
    }
  });
});

describe("Zero Trust stage guidance", () => {
  it("carries an explainer and a worked example for every CISA and DoD stage", () => {
    expect(ZT_STAGES.cisa_ztmm_2_0).toHaveLength(4);
    expect(ZT_STAGES.dod_ztra).toHaveLength(3);
    const examples: string[] = [];
    for (const [framework, stages] of Object.entries(ZT_STAGES)) {
      for (const stage of stages) {
        const guidance = ztStageGuidance(framework, stage);
        expect(guidance.explainer, `${framework} S${stage} explainer`).toMatch(
          /\S/,
        );
        expect(guidance.example, `${framework} S${stage} example`).toMatch(
          /\S/,
        );
        examples.push(guidance.example);
      }
    }
    expect(examples).toHaveLength(7);
    expect(new Set(examples).size).toBe(7);
  });

  it("refuses a stage the framework does not have", () => {
    // DoD ZTRA stops at 3; asking for a CISA-only stage 4 is a bug, not a blank.
    expect(() => ztStageGuidance("dod_ztra", 4)).toThrow(/4/);
    expect(() => ztStageGuidance("nist_zt", 1)).toThrow(/nist_zt/);
  });

  it("keeps stage labels and descriptions out of the guidance module", () => {
    for (const [framework, stages] of Object.entries(ZT_STAGES)) {
      for (const stage of stages) {
        expect(Object.keys(ztStageGuidance(framework, stage)).sort()).toEqual([
          "example",
          "explainer",
        ]);
      }
    }
  });
});
