import { proxyJson } from "../../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string; tier: string } },
) {
  return proxyJson(`/csf/services/${params.id}/profile/${params.tier}`, {
    method: "GET",
  });
}
