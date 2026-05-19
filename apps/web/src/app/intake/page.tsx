import type { Metadata } from "next";

import { IntakeWizard } from "@/components/intake/IntakeWizard";

export const metadata: Metadata = {
  title: "Intake",
};

export default function IntakePage(): JSX.Element {
  return <IntakeWizard />;
}
