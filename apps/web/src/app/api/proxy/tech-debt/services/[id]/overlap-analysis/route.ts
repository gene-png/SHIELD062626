import { proxyJson } from "../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/tech-debt/services/${params.id}/overlap-analysis`, {
    method: "GET",
  });
}
