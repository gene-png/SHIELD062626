"use client";

import { signOut, useSession } from "next-auth/react";
import * as React from "react";

import { REAUTH_REQUIRED_ERROR } from "@/lib/auth/errors";

/**
 * Watches the session for the daily forced-reauth / rotated-token signal
 * (`REAUTH_REQUIRED_ERROR`, set in the NextAuth refresh callback) and, when it
 * fires, clears the dead session and routes to sign-in with a friendly reason
 * banner instead of letting every proxy call 401 silently.
 *
 * Only the reauth signal triggers this. A generic refresh failure keeps the
 * existing per-proxy 401 behavior. Fresh sign-ins never carry the error, so
 * the e2e suite (24h ceiling, short-lived sessions) never trips it.
 */
export function SessionExpiryGuard(): null {
  const { data: session } = useSession();
  const firedRef = React.useRef(false);

  React.useEffect(() => {
    if (session?.error === REAUTH_REQUIRED_ERROR && !firedRef.current) {
      firedRef.current = true;
      void signOut({ callbackUrl: "/sign-in?reason=session_expired" });
    }
  }, [session?.error]);

  return null;
}
