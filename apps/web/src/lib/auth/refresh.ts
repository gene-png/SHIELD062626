/**
 * Server-side refresh chain cache (hotfix, D-034).
 *
 * Why this exists: the backend rotates refresh tokens (one active jti; a
 * replayed token reads as theft → reason=refresh_reused → forced sign-out),
 * but the Auth.js jwt callback runs in RSC and route-handler contexts that
 * can never write the rotated pair back to the session cookie. Every page
 * whose parallel server-side calls crossed the 15-minute access-token expiry
 * fired several refreshes with the same (soon stale) cookie token, and the
 * session died mid-use.
 *
 * The fix is a module-scoped cache keyed by the COOKIE's refresh token — the
 * root of that cookie's rotation chain:
 *   - a valid cached chain head is returned with zero network;
 *   - an expired head is advanced with a SINGLE in-flight refresh using the
 *     head's own refresh token (clean sequential rotation per process);
 *   - typed terminal failures are cached briefly so concurrent stragglers
 *     don't hammer /auth/refresh; transient failures are never cached;
 *   - chains untouched past the eviction horizon are dropped (their tokens
 *     are expired anyway, and the backend's anchored one-step reuse grace
 *     covers a cold-start replay after a web restart).
 *
 * When Auth.js's own /api/auth/session handler runs (provider mount, window
 * refocus) it flows through the same resolve() and persists the chain head to
 * the cookie — a healing side effect the design never depends on.
 */

import type { JWT } from "next-auth/jwt";

import { ApiError, apiFetch } from "@/lib/api";
import { REAUTH_REQUIRED_ERROR } from "@/lib/auth/errors";

/** Refresh this many ms early so an in-flight proxy call never races expiry. */
export const REFRESH_SKEW_MS = 30_000;

/** How long a typed terminal refresh failure answers stragglers from cache. */
export const TERMINAL_ERROR_CACHE_MS = 30_000;

/** Chains untouched this long are dropped (their tokens are long expired). */
export const CHAIN_EVICT_MS = 30 * 60_000;

/** Hard cap on tracked chains — one per active session cookie in practice. */
const MAX_CHAINS = 1000;

/** Mirrors the backend TokenPairResponse returned by POST /auth/refresh. */
interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
}

export type RefreshFetcher = typeof apiFetch;

interface ChainHead {
  accessToken: string;
  refreshToken: string;
  accessExpiresAt: string;
}

type RefreshOutcome =
  { head: ChainHead; error?: never } | { head?: never; error: string };

interface ChainEntry {
  head?: ChainHead;
  inflight?: Promise<RefreshOutcome>;
  terminal?: { error: string; at: number };
  touchedAt: number;
}

export interface TokenRefresher {
  resolve(token: JWT): Promise<JWT>;
}

/** Pull the typed `reason` out of the backend's {error:{reason}} envelope. */
export function reasonOf(payload: unknown): string | undefined {
  if (payload && typeof payload === "object" && "error" in payload) {
    const err = (payload as { error?: unknown }).error;
    if (err && typeof err === "object" && "reason" in err) {
      const reason = (err as { reason?: unknown }).reason;
      return typeof reason === "string" ? reason : undefined;
    }
  }
  return undefined;
}

function isFresh(accessExpiresAt: string | undefined, now: number): boolean {
  const expiresAt = accessExpiresAt ? Date.parse(accessExpiresAt) : 0;
  return Boolean(expiresAt) && now < expiresAt - REFRESH_SKEW_MS;
}

function withHead(token: JWT, head: ChainHead): JWT {
  return {
    ...token,
    accessToken: head.accessToken,
    refreshToken: head.refreshToken,
    accessExpiresAt: head.accessExpiresAt,
    error: undefined,
  };
}

/**
 * Build an isolated refresher (vitest injects a mock fetcher; production uses
 * the singleton below so every server context shares one chain cache).
 */
export function createTokenRefresher(
  fetcher: RefreshFetcher = apiFetch,
): TokenRefresher {
  const chains = new Map<string, ChainEntry>();

  function evict(now: number): void {
    for (const [key, entry] of chains) {
      if (now - entry.touchedAt > CHAIN_EVICT_MS) {
        chains.delete(key);
      }
    }
    if (chains.size > MAX_CHAINS) {
      // Pathological only (MAX_CHAINS concurrent sessions in one process);
      // drop the coldest chains rather than grow unbounded.
      const byAge = [...chains.entries()].sort(
        (a, b) => a[1].touchedAt - b[1].touchedAt,
      );
      for (const [key] of byAge.slice(0, chains.size - MAX_CHAINS)) {
        chains.delete(key);
      }
    }
  }

  async function doRefresh(
    entry: ChainEntry,
    cookieToken: string,
  ): Promise<RefreshOutcome> {
    const refreshWith = entry.head?.refreshToken ?? cookieToken;
    try {
      const refreshed = await fetcher<RefreshResponse>("/auth/refresh", {
        method: "POST",
        body: { refresh_token: refreshWith },
        // Refresh is not tenant-scoped; don't leak a cookie-derived X-Client-Id.
        clientId: "",
      });
      entry.head = {
        accessToken: refreshed.access_token,
        refreshToken: refreshed.refresh_token,
        accessExpiresAt: refreshed.access_expires_at,
      };
      entry.terminal = undefined;
      return { head: entry.head };
    } catch (err) {
      const reason =
        err instanceof ApiError ? reasonOf(err.payload) : undefined;
      const isTerminal =
        reason === "reauth_required" ||
        reason === "refresh_reused" ||
        reason === "refresh_expired";
      if (isTerminal) {
        console.error(
          `[auth.refresh] terminal refresh failure reason=${reason}`,
        );
        entry.terminal = { error: REAUTH_REQUIRED_ERROR, at: Date.now() };
        return { error: REAUTH_REQUIRED_ERROR };
      }
      console.error(
        `[auth.refresh] transient refresh failure: ${err instanceof Error ? err.message : String(err)}`,
      );
      return { error: "RefreshAccessTokenError" };
    }
  }

  async function resolve(token: JWT): Promise<JWT> {
    const now = Date.now();
    evict(now);

    // Still-valid access token: nothing to do (the common case).
    if (isFresh(token.accessExpiresAt, now)) {
      return token;
    }
    if (!token.refreshToken) {
      return { ...token, error: "RefreshAccessTokenError" };
    }

    let entry = chains.get(token.refreshToken);
    if (!entry) {
      entry = { touchedAt: now };
      chains.set(token.refreshToken, entry);
    }
    entry.touchedAt = now;

    // A stale cookie token rides the chain head minted by an earlier refresh.
    if (entry.head && isFresh(entry.head.accessExpiresAt, now)) {
      return withHead(token, entry.head);
    }

    // A just-failed terminal refresh answers stragglers without re-fetching.
    if (entry.terminal && now - entry.terminal.at < TERMINAL_ERROR_CACHE_MS) {
      return { ...token, error: entry.terminal.error };
    }

    // Single-flight: every concurrent caller awaits the same rotation.
    if (!entry.inflight) {
      const flight = doRefresh(entry, token.refreshToken);
      entry.inflight = flight;
      void flight.finally(() => {
        if (entry.inflight === flight) {
          entry.inflight = undefined;
        }
      });
    }
    const outcome = await entry.inflight;
    if (outcome.error !== undefined) {
      return { ...token, error: outcome.error };
    }
    return withHead(token, outcome.head);
  }

  return { resolve };
}

const defaultRefresher = createTokenRefresher();

/** The production entry point the jwt callback delegates to. */
export function resolveSessionToken(token: JWT): Promise<JWT> {
  return defaultRefresher.resolve(token);
}
