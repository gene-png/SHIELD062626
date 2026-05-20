import { proxyJson } from "../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/attack/services/${params.id}/heatmap`, { method: "GET" });
}
