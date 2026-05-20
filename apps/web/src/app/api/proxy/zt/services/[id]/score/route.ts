import { proxyJson } from "../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/zt/services/${params.id}/score`, { method: "GET" });
}
