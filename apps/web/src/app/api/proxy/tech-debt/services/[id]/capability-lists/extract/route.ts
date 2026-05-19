import { proxyJsonFromRequest } from "../../../../_proxy";

export async function POST(
  request: Request,
  { params }: { params: { id: string } },
) {
  return proxyJsonFromRequest(
    request,
    `/tech-debt/services/${params.id}/capability-lists/extract`,
    "POST",
  );
}
