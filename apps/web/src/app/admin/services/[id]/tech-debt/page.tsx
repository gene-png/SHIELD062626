import type { Metadata } from "next";

import { EnsureActiveClient } from "@/components/admin/EnsureActiveClient";
import { TechDebtWorkspace } from "@/components/admin/TechDebtWorkspace";

export const metadata: Metadata = {
  title: "Tech Debt service",
};

export default function TechDebtServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  // EnsureActiveClient aligns the active tenant to this service's client so the
  // workspace's tenant-scoped calls resolve. The service title is still a
  // placeholder until a service-detail fetch wires it through.
  return (
    <EnsureActiveClient serviceId={params.id}>
      <TechDebtWorkspace
        serviceId={params.id}
        serviceTitle="Tech Debt Review"
      />
    </EnsureActiveClient>
  );
}
