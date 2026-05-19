import { proxyJson } from "../../../../_proxy";

export async function POST(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/csf/services/${params.id}/deliverables/finalize`, {
    method: "POST",
  });
}
