import { proxyJson } from "../../../_proxy";

export async function GET(
  _request: Request,
  { params }: { params: { cid: string } },
) {
  return proxyJson(`/risk/clients/${params.cid}/gate`, { method: "GET" });
}
