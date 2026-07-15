/**
 * NextAuth configuration: Credentials provider hitting the FastAPI
 * /auth/login endpoint and storing the returned access + refresh tokens
 * in the encrypted JWT session.
 *
 * v1.x will swap the Credentials provider for a Keycloak OIDC provider
 * with the same `aud=shield-api` claim - no schema migration required.
 */

import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import CredentialsProvider from "next-auth/providers/credentials";

import { ApiError, apiFetch } from "@/lib/api";
import { REAUTH_REQUIRED_ERROR } from "@/lib/auth/errors";

interface LoginResponse {
  access_token: string | null;
  refresh_token: string | null;
  access_expires_at: string | null;
  refresh_expires_at: string | null;
  // MFA challenge branch (Sprint 6 T4, D-027). When the user has TOTP MFA
  // enrolled, /auth/login returns mfa_required=true + a short-lived pending
  // token instead of the pair; the pair arrives from /auth/mfa/verify-login.
  mfa_required?: boolean;
  mfa_pending_token?: string | null;
}

/**
 * Thrown out of `authorize` to tell the sign-in form that the password was
 * correct but a TOTP code is still required. NextAuth surfaces the message as
 * `result.error`, which the form matches to reveal the code field.
 */
const MFA_REQUIRED_ERROR = "mfa_required";

/** Mirrors the backend TokenPairResponse returned by POST /auth/refresh, which
 * always yields a full (non-null) pair — unlike /auth/login, which can return
 * an MFA challenge instead. */
interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
}

/** Refresh this many ms early so an in-flight proxy call never races expiry. */
const REFRESH_SKEW_MS = 30_000;

/** Pull the typed `reason` out of the backend's {error:{reason}} envelope. */
function reasonOf(payload: unknown): string | undefined {
  if (payload && typeof payload === "object" && "error" in payload) {
    const err = (payload as { error?: unknown }).error;
    if (err && typeof err === "object" && "reason" in err) {
      const reason = (err as { reason?: unknown }).reason;
      return typeof reason === "string" ? reason : undefined;
    }
  }
  return undefined;
}

/**
 * Trade the stored refresh token for a fresh access+refresh pair.
 *
 * The backend access token lives 15 min while the NextAuth session lives
 * 24 h, so without this the session keeps handing proxies a dead bearer and
 * every upstream call 401s. On failure we stamp the token with an error so
 * `session()` stops exposing the access token and the UI falls back to
 * sign-in. A backend `reauth_required` / `refresh_reused` reason (daily
 * forced-reauth ceiling, or a rotated-out token) is surfaced as the distinct
 * REAUTH_REQUIRED_ERROR so the UI can show friendly "please sign in again"
 * copy rather than a generic error.
 */
async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken) {
    return { ...token, error: "RefreshAccessTokenError" };
  }
  try {
    const refreshed = await apiFetch<RefreshResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: token.refreshToken },
      // Refresh is not tenant-scoped; don't leak a cookie-derived X-Client-Id.
      clientId: "",
    });
    return {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token,
      accessExpiresAt: refreshed.access_expires_at,
      error: undefined,
    };
  } catch (err) {
    const reason = err instanceof ApiError ? reasonOf(err.payload) : undefined;
    const isReauth =
      reason === "reauth_required" || reason === "refresh_reused";
    return {
      ...token,
      error: isReauth ? REAUTH_REQUIRED_ERROR : "RefreshAccessTokenError",
    };
  }
}

interface MeResponse {
  id: string;
  email: string;
  role: "admin" | "client";
  display_name: string | null;
}

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt", maxAge: 60 * 60 * 24 },
  pages: { signIn: "/sign-in" },
  providers: [
    CredentialsProvider({
      name: "Email + password",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        // Optional second factor. Absent on the first submit; the form re-submits
        // with it after we signal MFA_REQUIRED.
        totp: { label: "Authenticator code", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          const login = await apiFetch<LoginResponse>("/auth/login", {
            method: "POST",
            body: { email: credentials.email, password: credentials.password },
          });

          let tokens: LoginResponse = login;
          if (login.mfa_required) {
            // Password was correct but a second factor is needed. Without a code
            // yet, tell the form to prompt for one. With a code, exchange the
            // pending token for the real pair.
            if (!credentials.totp) {
              throw new Error(MFA_REQUIRED_ERROR);
            }
            tokens = await apiFetch<LoginResponse>("/auth/mfa/verify-login", {
              method: "POST",
              body: {
                mfa_pending_token: login.mfa_pending_token,
                code: credentials.totp,
              },
            });
          }

          if (!tokens.access_token || !tokens.refresh_token) {
            return null;
          }
          const me = await apiFetch<MeResponse>("/auth/me", {
            bearer: tokens.access_token,
          });
          const user: import("next-auth").User = {
            id: me.id,
            email: me.email,
            name: me.display_name ?? me.email,
            role: me.role,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            accessExpiresAt: tokens.access_expires_at ?? undefined,
          };
          return user;
        } catch (err) {
          if (err instanceof Error && err.message === MFA_REQUIRED_ERROR) {
            // Re-throw so NextAuth surfaces it as result.error to the form.
            throw err;
          }
          if (
            err instanceof ApiError &&
            (err.status === 401 || err.status === 423)
          ) {
            // Wrong password / locked / wrong-or-expired MFA code → generic.
            return null;
          }
          throw err;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign-in: seed the token from the authorized user.
      if (user) {
        token.role = user.role;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessExpiresAt = user.accessExpiresAt;
        token.error = undefined;
        return token;
      }
      // Subsequent calls: keep the access token alive while it's still valid,
      // otherwise rotate it via the refresh token before any proxy reads it.
      const expiresAt = token.accessExpiresAt
        ? Date.parse(token.accessExpiresAt)
        : 0;
      if (expiresAt && Date.now() < expiresAt - REFRESH_SKEW_MS) {
        return token;
      }
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.role = token.role;
      // Don't hand out a token we know is dead; surface the error so the UI
      // can route back to sign-in instead of silently 401ing on every proxy.
      session.accessToken = token.error ? undefined : token.accessToken;
      session.error = token.error;
      return session;
    },
  },
};
