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

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
}

/** Mirrors the backend TokenPairResponse returned by POST /auth/refresh. */
type RefreshResponse = LoginResponse;

/** Refresh this many ms early so an in-flight proxy call never races expiry. */
const REFRESH_SKEW_MS = 30_000;

/**
 * Trade the stored refresh token for a fresh access+refresh pair.
 *
 * The backend access token lives 15 min while the NextAuth session lives
 * 24 h, so without this the session keeps handing proxies a dead bearer and
 * every upstream call 401s. On failure (e.g. the 30-min refresh TTL lapsed
 * while idle) we stamp the token with an error so `session()` stops exposing
 * the access token and the UI falls back to sign-in.
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
  } catch {
    return { ...token, error: "RefreshAccessTokenError" };
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
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          const tokens = await apiFetch<LoginResponse>("/auth/login", {
            method: "POST",
            body: { email: credentials.email, password: credentials.password },
          });
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
            accessExpiresAt: tokens.access_expires_at,
          };
          return user;
        } catch (err) {
          if (
            err instanceof ApiError &&
            (err.status === 401 || err.status === 423)
          ) {
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
