import { proxyJson } from "../../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/tech-debt/services/${params.id}/capability-lists/latest`, {
    method: "GET",
  });
}
