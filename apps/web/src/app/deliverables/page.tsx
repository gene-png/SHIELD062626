import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import {
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  StatusPill,
} from "@shield/design-system";

import { PublicFooter } from "@/components/site/PublicFooter";
import { PublicHeader } from "@/components/site/PublicHeader";
import { SelectClientPrompt } from "@/components/site/SelectClientPrompt";
import { ApiError, apiFetch } from "@/lib/api";
import { authOptions } from "@/lib/auth/options";
import type { ReleasedDeliverableList } from "@/lib/deliverables/types";

function fmtDate(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default async function DeliverablesPage(): Promise<JSX.Element> {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/sign-in?callbackUrl=/deliverables");
  }
  let list: ReleasedDeliverableList = { items: [] };
  let loadError: string | null = null;
  let needsClient = false;
  try {
    list = await apiFetch<ReleasedDeliverableList>("/deliverables", {
      bearer: session.accessToken,
    });
  } catch (err) {
    // Admin/reviewer with no active client selected: backend returns 400
    // "X-Client-Id required". Surface the client picker instead of a raw error.
    if (err instanceof ApiError && err.status === 400) {
      needsClient = true;
    } else {
      loadError =
        err instanceof Error ? err.message : "Failed to load deliverables.";
    }
  }
  return (
    <>
      <PublicHeader />
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <header className="mb-8 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">
            Your engagement
          </p>
          <h1 className="text-3xl font-semibold text-ink-primary">
            Released deliverables
          </h1>
          <p className="max-w-prose text-sm text-ink-secondary">
            Final PDF reports + the supporting XLSX capability list for every
            released service. The PDF is the executive-ready summary; the XLSX
            is the underlying inventory with disposition decisions.
          </p>
        </header>
        {needsClient ? (
          <SelectClientPrompt action="view deliverables" />
        ) : loadError ? (
          <Card>
            <CardHeader>
              <CardTitle>Couldn&apos;t load deliverables</CardTitle>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-status-danger-fg">{loadError}</p>
            </CardBody>
          </Card>
        ) : list.items.length === 0 ? (
          <EmptyState
            title="No released deliverables yet"
            description="When your consultant releases a finalized report, it will appear here. You'll also receive an in-app notification."
          />
        ) : (
          <ul className="flex flex-col gap-4">
            {list.items.map((d) => (
              <li key={d.id}>
                <Card>
                  <CardHeader>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <CardTitle>{d.service_title}</CardTitle>
                      <StatusPill tone="success" withDot>
                        Released v{d.version}
                      </StatusPill>
                    </div>
                  </CardHeader>
                  <CardBody className="flex flex-col gap-3">
                    {d.summary ? (
                      <p className="text-sm text-ink-secondary">{d.summary}</p>
                    ) : null}
                    <ul className="space-y-1 text-sm">
                      {d.pdf_artifact_id ? (
                        <li>
                          <a
                            href={`/api/proxy/artifacts/${d.pdf_artifact_id}/download`}
                            className="text-brand-500 underline hover:text-brand-600"
                          >
                            {d.pdf_filename ?? "Download PDF"}
                          </a>
                        </li>
                      ) : null}
                      {d.xlsx_artifact_id ? (
                        <li>
                          <a
                            href={`/api/proxy/artifacts/${d.xlsx_artifact_id}/download`}
                            className="text-brand-500 underline hover:text-brand-600"
                          >
                            {d.xlsx_filename ?? "Download XLSX"}
                          </a>
                        </li>
                      ) : null}
                    </ul>
                    <p className="text-xs text-ink-tertiary">
                      Released {fmtDate(d.released_to_client_at)}
                    </p>
                  </CardBody>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </main>
      <PublicFooter />
    </>
  );
}
