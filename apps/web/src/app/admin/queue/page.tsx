import type { Metadata } from "next";

import { IntakeQueue } from "@/components/admin/IntakeQueue";

export const metadata: Metadata = {
  title: "Intake queue",
};

export default function AdminQueuePage(): JSX.Element {
  return <IntakeQueue />;
}
