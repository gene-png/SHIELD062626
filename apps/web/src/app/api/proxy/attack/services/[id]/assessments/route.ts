import { proxyJsonFromRequest } from "../../../_proxy";

export async function POST(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(
    request,
    `/attack/services/${params.id}/assessments`,
    "POST",
  );
}
