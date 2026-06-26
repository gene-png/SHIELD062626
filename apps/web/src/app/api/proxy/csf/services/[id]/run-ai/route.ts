import { proxyJson } from "../../../_proxy";

export async function POST(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/csf/services/${params.id}/run-ai`, { method: "POST" });
}
