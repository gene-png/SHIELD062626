import { proxyJsonFromRequest } from "../../_proxy";

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(request, `/zt/answers/${params.id}`, "PATCH");
}
