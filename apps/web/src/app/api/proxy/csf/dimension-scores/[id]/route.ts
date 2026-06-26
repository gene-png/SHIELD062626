import { proxyJsonFromRequest } from "../../_proxy";

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(
    request,
    `/csf/dimension-scores/${params.id}`,
    "PATCH",
  );
}
