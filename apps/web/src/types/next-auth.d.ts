import type { DefaultSession, DefaultUser } from "next-auth";

declare module "next-auth" {
  interface Session extends DefaultSession {
    role?: "admin" | "reviewer" | "client";
    accessToken?: string;
    error?: string;
  }
  interface User extends DefaultUser {
    role?: "admin" | "reviewer" | "client";
    accessToken?: string;
    refreshToken?: string;
    accessExpiresAt?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: "admin" | "reviewer" | "client";
    accessToken?: string;
    refreshToken?: string;
    accessExpiresAt?: string;
    error?: string;
  }
}
