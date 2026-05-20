import { proxyJson } from "../../../_proxy";

export async function GET(
  request: Request,
  { params }: { params: { id: string } },
) {
  const incoming = new URL(request.url).searchParams.toString();
  const upstream = `/zt/services/${params.id}/gap-analysis${incoming ? `?${incoming}` : ""}`;
  return proxyJson(upstream, { method: "GET" });
}
