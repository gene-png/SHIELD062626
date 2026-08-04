/**
 * Answering aids for the Zero Trust questionnaire (S6).
 *
 * The two frameworks run different-length ladders, so guidance is keyed by
 * framework and stage: CISA ZTMM 2.0 has 4 stages, DoD ZTRA has 3. Stage labels
 * and full descriptions arrive on the catalog payload the API builds from
 * `CISA_STAGES` and `DOD_STAGES`; this file adds only the explainer and the
 * worked example, so there is no label copy here to drift.
 */

import type { ZtFramework } from "@/lib/zt/types";

import type { LevelGuidance } from "./csf";

/** Stages each framework actually offers, in ladder order. */
export const ZT_STAGES: Record<ZtFramework, readonly number[]> = {
  cisa_ztmm_2_0: [1, 2, 3, 4],
  dod_ztra: [1, 2, 3],
};

const STAGE_GUIDANCE: Record<ZtFramework, Record<number, LevelGuidance>> = {
  cisa_ztmm_2_0: {
    1: {
      explainer:
        "Trust is decided at the network edge. Once someone is inside the perimeter or on the VPN, the systems behind it stop asking who they are.",
      example:
        "Staff sign in to the VPN once in the morning, then reach the file shares, the finance app, and the admin console with no further check.",
    },
    2: {
      explainer:
        "You verify who someone is and you know what you own, and after the sign-in the session keeps its access until it ends.",
      example:
        "MFA is switched on at the identity provider and the device inventory is current. A laptop that fails its patch check keeps working until the user signs out.",
    },
    3: {
      explainer:
        "Identity, device, and network signals are read together, and access changes when the risk changes, for the conditions you have written down.",
      example:
        "A sign-in from an unmanaged device drops to read-only on its own, because one policy evaluates the account and the device posture together.",
    },
    4: {
      explainer:
        "Trust is rechecked continuously instead of at the door, access is granted for a task and then expires, and the analytics correct the policy.",
      example:
        "An engineer gets admin rights for one change window, the grant expires without anyone revoking it, and a device that drifts out of policy loses access mid-session.",
    },
  },
  dod_ztra: {
    1: {
      explainer:
        "Basic hygiene is in place and no Zero Trust activity has been adopted for this capability yet.",
      example:
        "Accounts have passwords and the servers are patched. No Zero Trust activity for this capability has been assigned an owner or a budget.",
    },
    2: {
      explainer:
        "The foundational Zero Trust activities for this capability are implemented, which is what the DoD strategy sets as the FY27 target phase.",
      example:
        "Every user holds one authoritative identity with MFA, device compliance is checked before access is granted, and the activity list for this capability is complete.",
    },
    3: {
      explainer:
        "The capability is integrated with the pillars around it and keeps adjusting to what its telemetry shows.",
      example:
        "Access decisions read live device and behaviour telemetry, and the policy is retuned from what those decisions produce.",
    },
  },
};

function assertFramework(framework: string): ZtFramework {
  const known = Object.keys(ZT_STAGES).find((f) => f === framework);
  if (known === undefined) {
    throw new Error(
      `[guidance/zt] no guidance for framework "${framework}"; known frameworks are ${Object.keys(
        ZT_STAGES,
      ).join(", ")}`,
    );
  }
  return known as ZtFramework;
}

/**
 * Explainer plus worked example for one stage of one framework. Throws rather
 * than returning a blank: asking DoD ZTRA for a stage 4 is a bug in the caller,
 * not an empty disclosure for the client to puzzle over.
 */
export function ztStageGuidance(
  framework: string,
  stage: number,
): LevelGuidance {
  const code = assertFramework(framework);
  const guidance = STAGE_GUIDANCE[code][stage];
  if (!guidance) {
    throw new Error(
      `[guidance/zt] no guidance for ${code} stage ${stage}; that framework offers stages ${ZT_STAGES[
        code
      ].join(", ")}`,
    );
  }
  return guidance;
}
