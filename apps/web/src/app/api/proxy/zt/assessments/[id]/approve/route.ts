import { proxyJson } from "../../../_proxy";

export async function POST(
  _request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJson(`/zt/assessments/${params.id}/approve`, { method: "POST" });
}
