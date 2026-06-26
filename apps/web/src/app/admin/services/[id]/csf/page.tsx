import type { Metadata } from "next";

import { CsfWorkspace } from "@/components/admin/csf/CsfWorkspace";
import { EnsureActiveClient } from "@/components/admin/EnsureActiveClient";

export const metadata: Metadata = {
  title: "NIST CSF 2.0 service",
};

export default function CsfServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  return (
    <EnsureActiveClient serviceId={params.id}>
      <CsfWorkspace
        serviceId={params.id}
        serviceTitle="NIST CSF 2.0 Assessment"
      />
    </EnsureActiveClient>
  );
}
