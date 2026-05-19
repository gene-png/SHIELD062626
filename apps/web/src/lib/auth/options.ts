/**
 * NextAuth configuration: Credentials provider hitting the FastAPI
 * /auth/login endpoint and storing the returned access + refresh tokens
 * in the encrypted JWT session.
 *
 * v1.x will swap the Credentials provider for a Keycloak OIDC provider
 * with the same `aud=shield-api` claim - no schema migration required.
 */

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

import { ApiError, apiFetch } from "@/lib/api";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
}

interface MeResponse {
  id: string;
  email: string;
  role: "admin" | "reviewer" | "client";
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
          if (err instanceof ApiError && (err.status === 401 || err.status === 423)) {
            return null;
          }
          throw err;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessExpiresAt = user.accessExpiresAt;
      }
      return token;
    },
    async session({ session, token }) {
      session.role = token.role;
      session.accessToken = token.accessToken;
      return session;
    },
  },
};
