import {
  Card,
  CardBody,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@shield/design-system";

const SERVICES: { title: string; description: string }[] = [
  {
    title: "Technical Debt Review",
    description:
      "Inventory the security stack, surface overlap and gaps, produce a defensible consolidation plan.",
  },
  {
    title: "Zero Trust Assessment",
    description:
      "Score current and target maturity per pillar against CISA ZTMM 2.0 or the DoD Zero Trust Reference Architecture.",
  },
  {
    title: "NIST CSF 2.0 Assessment",
    description:
      "Run the full 10-step Playbook with HIGH / MODERATE / LOW tiered profiles, 5-dimension scoring, weighted-floor roll-up, and a prioritized gap plan.",
  },
  {
    title: "MITRE ATT&CK Coverage",
    description:
      "Score the full Enterprise matrix against the approved capability list. Detect, prevent, and respond columns reconciled with a clear roadmap.",
  },
];

export function ServiceGrid(): JSX.Element {
  return (
    <section
      aria-labelledby="services-heading"
      className="mx-auto max-w-6xl px-6 py-16"
    >
      <h2
        id="services-heading"
        className="text-2xl font-semibold text-ink-primary"
      >
        Four assessments. One operating system.
      </h2>
      <p className="mt-2 max-w-2xl text-ink-secondary">
        Each service ships in-app with editable workspaces, plain-English client
        views, and PDF + XLSX deliverables that follow your filename
        conventions.
      </p>
      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {SERVICES.map((s) => (
          <Card key={s.title}>
            <CardHeader>
              <CardTitle>{s.title}</CardTitle>
              <CardDescription>{s.description}</CardDescription>
            </CardHeader>
            <CardBody>
              <p className="text-xs uppercase tracking-wider text-ink-tertiary">
                Includes:
                <span className="ml-2 normal-case tracking-normal text-ink-secondary">
                  reviewer audit walk, exec rollup, audit-logged AI extractions.
                </span>
              </p>
            </CardBody>
          </Card>
        ))}
      </div>
    </section>
  );
}
