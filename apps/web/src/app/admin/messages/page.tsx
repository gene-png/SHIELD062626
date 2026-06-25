import type { Metadata } from "next";
import Link from "next/link";

import { Card, CardBody } from "@shield/design-system";

import { Breadcrumbs } from "@/components/site/Breadcrumbs";

export const metadata: Metadata = { title: "Messages" };

export default function AdminMessagesPage(): JSX.Element {
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs items={[{ label: "Messages" }]} />
      <div>
        <h1 className="text-2xl font-semibold text-ink-primary">Messages</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Client threads that need a reply.
        </p>
      </div>
      <Card>
        <CardBody className="flex flex-col items-start gap-3">
          <p className="text-sm text-ink-secondary">
            Message threads live on each service. Open a client&apos;s service
            from the intake queue to read and reply; a cross-client inbox lands
            with the service workspaces.
          </p>
          <Link
            href="/admin/queue"
            className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600"
          >
            Go to the intake queue
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}
