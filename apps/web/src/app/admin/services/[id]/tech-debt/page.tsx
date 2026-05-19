import type { Metadata } from "next";

import { TechDebtWorkspace } from "@/components/admin/TechDebtWorkspace";

export const metadata: Metadata = {
  title: "Tech Debt service",
};

export default function TechDebtServicePage({
  params,
}: {
  params: { id: string };
}): JSX.Element {
  // Stage 5 baseline: we don't yet have a /tech-debt/services/{id} GET on
  // the API. The workspace component pulls the latest list on mount; the
  // service title is a sensible placeholder until stage 9 wires the
  // service-detail fetch. The page is admin-gated by app/admin/layout.tsx
  // (Phase 2 stage 7).
  return (
    <TechDebtWorkspace serviceId={params.id} serviceTitle="Tech Debt Review" />
  );
}
