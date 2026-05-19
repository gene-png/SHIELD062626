/**
 * Multipart proxy for /artifacts. The Next.js route reads the inbound
 * FormData, attaches the session's access token, and forwards to the
 * FastAPI upload endpoint. The browser never sees the API host name or
 * the access token.
 */

import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";

import { authOptions } from "@/lib/auth/options";

const BASE_URL = process.env.API_BASE_URL ?? "http://api:8000";

async function bearerOrUnauthorized(): Promise<string | NextResponse> {
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  if (!token) {
    return NextResponse.json(
      { error: { code: 401, message: "Not signed in." } },
      { status: 401 },
    );
  }
  return token;
}

export async function POST(request: Request): Promise<NextResponse> {
  const bearer = await bearerOrUnauthorized();
  if (bearer instanceof NextResponse) return bearer;

  // Forward the FormData payload as-is so multipart boundaries and the
  // raw file bytes are preserved.
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json(
      { error: { code: 400, message: "Multipart body required." } },
      { status: 400 },
    );
  }

  const upstream = await fetch(`${BASE_URL}/artifacts`, {
    method: "POST",
    headers: { Authorization: `Bearer ${bearer}` },
    body: form,
  });
  const body = await upstream.text();
  try {
    return new NextResponse(body, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { error: { message: "Upstream upload failed." } },
      { status: 502 },
    );
  }
}

export async function GET(): Promise<NextResponse> {
  const bearer = await bearerOrUnauthorized();
  if (bearer instanceof NextResponse) return bearer;
  const upstream = await fetch(`${BASE_URL}/artifacts`, {
    headers: { Authorization: `Bearer ${bearer}` },
    cache: "no-store",
  });
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "application/json",
    },
  });
}
