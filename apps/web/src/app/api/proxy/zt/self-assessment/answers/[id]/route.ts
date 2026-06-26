import { proxyJsonFromRequest } from "../../../_proxy";

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(
    request,
    `/zt/self-assessment/answers/${params.id}`,
    "PATCH",
  );
}
