import type { Metadata } from "next";

import { EngagementsView } from "@/components/engagements/EngagementsView";

export const metadata: Metadata = {
  title: "My engagements",
};

export default function EngagementsPage(): JSX.Element {
  return <EngagementsView />;
}
