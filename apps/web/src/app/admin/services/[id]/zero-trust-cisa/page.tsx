import type { Metadata } from "next";

import { EnsureActiveClient } from "@/components/admin/EnsureActiveClient";
import { ZtWorkspace } from "@/components/admin/zt/ZtWorkspace";

export const metadata: Metadata = {
  title: "Zero Trust (CISA ZTMM 2.0) service",
};

export default function ZtCisaServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  return (
    <EnsureActiveClient serviceId={params.id}>
      <ZtWorkspace
        serviceId={params.id}
        framework="cisa_ztmm_2_0"
        serviceTitle="Zero Trust Assessment — CISA ZTMM 2.0"
      />
    </EnsureActiveClient>
  );
}
