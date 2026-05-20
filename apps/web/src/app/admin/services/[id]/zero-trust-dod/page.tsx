import type { Metadata } from "next";

import { ZtWorkspace } from "@/components/admin/zt/ZtWorkspace";

export const metadata: Metadata = {
  title: "Zero Trust (DoD ZTRA) service",
};

export default function ZtDodServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  return (
    <ZtWorkspace
      serviceId={params.id}
      framework="dod_ztra"
      serviceTitle="Zero Trust Assessment — DoD Reference Architecture"
    />
  );
}
