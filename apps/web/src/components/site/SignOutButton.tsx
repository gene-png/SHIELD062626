"use client";

import { signOut } from "next-auth/react";

/**
 * Client-side sign-out control. Clears the NextAuth session and returns the
 * user to the public landing page.
 */
export function SignOutButton(): JSX.Element {
  return (
    <button
      type="button"
      onClick={() => void signOut({ callbackUrl: "/" })}
      className="rounded-md px-3 py-2 font-medium text-ink-secondary hover:text-ink-primary"
    >
      Sign out
    </button>
  );
}
