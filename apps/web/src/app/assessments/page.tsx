import type { Metadata } from "next";

import { AssessmentsView } from "@/components/assessments/AssessmentsView";

export const metadata: Metadata = {
  title: "My assessments",
};

export default function AssessmentsPage(): JSX.Element {
  return <AssessmentsView />;
}
