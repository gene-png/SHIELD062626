import { proxyJsonFromRequest } from "../../../../_proxy";

export async function POST(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(
    request,
    `/csf/services/${params.id}/self-assessment/submit`,
    "POST",
  );
}
