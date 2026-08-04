/**
 * Answering aids for the CSF 2.0 questionnaire (S6).
 *
 * A client picking a maturity tier gets three things on screen: the tier label
 * and full description, both of which travel on the catalog payload the API
 * builds from `TIER_DEFINITIONS`, plus the two pieces here. The explainer says
 * what the tier means without framework vocabulary. The worked example says what
 * that tier looks like inside the function being asked about.
 *
 * Nothing in this file restates a label or a description. Those stay on the
 * backend side of the wire so the two cannot drift, which is what
 * `guidance.test.ts` pins.
 */

export const CSF_FUNCTION_CODES = ["GV", "ID", "PR", "DE", "RS", "RC"] as const;

export type CsfFunctionCode = (typeof CSF_FUNCTION_CODES)[number];

export const CSF_TIERS = [1, 2, 3, 4] as const;

export type CsfTier = (typeof CSF_TIERS)[number];

export interface LevelGuidance {
  /** What the level means, in words a non-specialist already uses. */
  explainer: string;
  /** What that level looks like for the function being answered. */
  example: string;
}

/**
 * One explainer per tier, shared across all six functions. Each one stays inside
 * what the NIST tier definition claims: tier 3 is organization-wide and written
 * down, and only tier 4 learns from what happened.
 */
const TIER_EXPLAINERS: Record<CsfTier, string> = {
  1: "Someone deals with this when it comes up, and which someone it is decides how well it goes. Nothing is written down, so the work starts over each time.",
  2: "Management has agreed how this should work. The agreement covers some teams and not others, and the people it affects often have not been told.",
  3: "A written policy covers the whole organization, it is reviewed on a set schedule, and the people it affects can find it.",
  4: "The policy changes when you learn something. Incidents and measurements feed back into it, and the same standard shapes who you buy from.",
};

/**
 * One worked example per function per tier (6 x 4). Each is a situation a client
 * can recognize in their own organization, and it names the tool, the document,
 * or the person that makes it true.
 */
const WORKED_EXAMPLES: Record<CsfFunctionCode, Record<CsfTier, string>> = {
  GV: {
    1: "A security policy was written for an audit two years ago. Nobody has opened it since and no one is named as its owner.",
    2: "Your leadership team approved a security policy. IT works to it; sales and finance have never been shown it.",
    3: "A named executive owns the security policy, every department is in scope, and it is reviewed on the same date each year.",
    4: "Last quarter's phishing incident changed the policy, and the same requirement now appears in the contracts you sign with suppliers.",
  },
  ID: {
    1: "You find out a laptop exists when its user opens a ticket. The asset list is a spreadsheet last saved two years ago.",
    2: "IT keeps an inventory of the servers in the data center. Laptops, phones, and cloud accounts get counted by whoever remembers.",
    3: "One inventory pulls in every device and cloud account through an agent or an API, and each entry records an owner.",
    4: "The inventory raises a flag the day a device stops checking in, and what those gaps reveal changes how new hardware is issued.",
  },
  PR: {
    1: "New staff get access by copying whoever sat in the chair before them. Leavers keep their accounts until somebody notices.",
    2: "A joiner and leaver checklist exists and HR follows it for employees. Contractors and shared logins are handled case by case.",
    3: "Access is granted by role, MFA is enforced for every account in the identity provider, reviews run quarterly, and each exception is written down with a reason.",
    4: "Each access review is shaped by what the last one found. A role that keeps collecting permissions gets redesigned, and suppliers have to meet the same rule.",
  },
  DE: {
    1: "You hear that something is wrong from a user or a customer. Logs sit on the machines that produce them and nobody reads them.",
    2: "Your firewall and endpoint tool email alerts to a shared mailbox. Someone opens it during office hours when there is time.",
    3: "Logs from every in-scope system land in one place, the alert rules are documented, and a named team reviews them on a defined schedule.",
    4: "Alert rules are retuned from what the last investigation showed, and a rule that only ever produces noise is retired rather than ignored.",
  },
  RS: {
    1: "When something happens, the response is whoever is free and whatever they think of. Nothing is recorded afterwards.",
    2: "An incident plan exists and the IT team knows it. Legal, communications, and your executives learn their part during the incident.",
    3: "A written incident plan names the roles, the contact numbers, and the reporting deadlines, and it applies to the whole organization.",
    4: "Every incident closes with a review that changes the plan, and the most recent change came out of a real event rather than a template.",
  },
  RC: {
    1: "Backups run and no one has tried a restore. The order things come back in would be decided during the outage.",
    2: "Backups run nightly for the systems IT knows about and one restore has been tested. No agreed order exists for bringing services back.",
    3: "A recovery plan lists systems in priority order with a target restore time for each, restores are tested on a schedule, and the results are recorded.",
    4: "Restore test results drive the plan. When a system misses its target time, either the target or the design changes, and affected customers hear from you on a known cadence.",
  },
};

function assertTier(tier: number): CsfTier {
  const known = CSF_TIERS.find((t) => t === tier);
  if (known === undefined) {
    throw new Error(
      `[guidance/csf] no guidance for maturity tier ${tier}; known tiers are ${CSF_TIERS.join(", ")}`,
    );
  }
  return known;
}

function assertFunctionCode(functionCode: string): CsfFunctionCode {
  const known = CSF_FUNCTION_CODES.find((c) => c === functionCode);
  if (known === undefined) {
    throw new Error(
      `[guidance/csf] no guidance for CSF function "${functionCode}"; known functions are ${CSF_FUNCTION_CODES.join(", ")}`,
    );
  }
  return known;
}

/** Plain-language explainer for a tier. Throws on an unknown tier. */
export function csfTierExplainer(tier: number): string {
  return TIER_EXPLAINERS[assertTier(tier)];
}

/**
 * Explainer plus the function-specific worked example for one tier. Throws
 * rather than returning a blank, so a missing entry surfaces as an error instead
 * of an empty disclosure that reads as "no guidance exists".
 */
export function csfLevelGuidance(
  functionCode: string,
  tier: number,
): LevelGuidance {
  const code = assertFunctionCode(functionCode);
  const level = assertTier(tier);
  const example = WORKED_EXAMPLES[code][level];
  if (!example) {
    throw new Error(
      `[guidance/csf] missing worked example for ${code} tier ${level}`,
    );
  }
  return { explainer: TIER_EXPLAINERS[level], example };
}
