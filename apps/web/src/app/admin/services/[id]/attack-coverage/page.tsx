import type { Metadata } from "next";

import { AttackWorkspace } from "@/components/admin/attack/AttackWorkspace";

export const metadata: Metadata = {
  title: "MITRE ATT&CK Coverage service",
};

export default function AttackCoverageServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  return (
    <AttackWorkspace
      serviceId={params.id}
      serviceTitle="MITRE ATT&CK Coverage"
    />
  );
}
