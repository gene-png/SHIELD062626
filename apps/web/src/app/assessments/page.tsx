import type { Metadata } from "next";

import { AssessmentsView } from "@/components/assessments/AssessmentsView";
import { PublicFooter } from "@/components/site/PublicFooter";
import { PublicHeader } from "@/components/site/PublicHeader";

export const metadata: Metadata = {
  title: "My assessments",
};

export default function AssessmentsPage(): JSX.Element {
  return (
    <>
      <PublicHeader />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <AssessmentsView />
      </main>
      <PublicFooter />
    </>
  );
}
