import { proxyJson } from "../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/csf/services/${params.id}/questionnaire`, {
    method: "GET",
  });
}
