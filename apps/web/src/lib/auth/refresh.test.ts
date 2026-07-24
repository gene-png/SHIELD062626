/**
 * Chain-cache refresh tests (hotfix, D-034).
 *
 * The jwt callback used to fire one bare /auth/refresh per concurrent caller
 * with whatever refresh token the cookie carried. Backend rotation treats a
 * replayed token as theft, so a burst of parallel server-side calls (or any
 * call after the cookie went stale, which RSC contexts can never heal) ended
 * the session ~15 minutes in. These tests pin the fix: one in-flight refresh
 * per chain, a cached chain head for stale-cookie callers, chain advance on
 * the head's token, typed-reason mapping, and eviction of dead chains.
 */

import type { JWT } from "next-auth/jwt";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";
import { REAUTH_REQUIRED_ERROR } from "./errors";
import { createTokenRefresher } from "./refresh";
import type { RefreshFetcher } from "./refresh";

const MINUTE = 60_000;

function isoIn(ms: number): string {
  return new Date(Date.now() + ms).toISOString();
}

/** A session JWT whose access token has already lapsed (forces a refresh). */
function staleJwt(overrides: Partial<JWT> = {}): JWT {
  return {
    role: "admin",
    accessToken: "A0",
    refreshToken: "R0",
    accessExpiresAt: isoIn(-1000),
    error: undefined,
    ...overrides,
  } as JWT;
}

/** Backend TokenPairResponse for generation `n`, access valid 15 min. */
function pair(n: number) {
  return {
    access_token: `A${n}`,
    refresh_token: `R${n}`,
    access_expires_at: isoIn(15 * MINUTE),
    refresh_expires_at: isoIn(30 * MINUTE),
  };
}

function pairFetcher(): ReturnType<typeof vi.fn> {
  let generation = 0;
  return vi.fn(async () => {
    generation += 1;
    // Yield the microtask queue so concurrent resolve() calls overlap.
    await Promise.resolve();
    return pair(generation);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-07-24T12:00:00Z"));
});

afterEach(() => {
  vi.useRealTimers();
});

describe("createTokenRefresher", () => {
  it("coalesces concurrent refreshes into a single backend call", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const token = staleJwt();
    const [a, b, c] = await Promise.all([
      refresher.resolve(token),
      refresher.resolve(token),
      refresher.resolve(token),
    ]);

    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(a.accessToken).toBe("A1");
    expect(b.accessToken).toBe("A1");
    expect(c.accessToken).toBe("A1");
    expect(a.error).toBeUndefined();
  });

  it("serves the cached chain head to stale-cookie callers with zero network", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const token = staleJwt();
    await refresher.resolve(token);

    // The same stale cookie token arrives again (RSC contexts never persist
    // the rotated pair back to the cookie) — it must ride the cached head.
    const again = await refresher.resolve(token);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(again.accessToken).toBe("A1");
    expect(again.refreshToken).toBe("R1");
    expect(again.error).toBeUndefined();
  });

  it("advances the chain using the head's refresh token, not the cookie's", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const token = staleJwt();
    await refresher.resolve(token);

    // Head A1/R1 expires; the next resolve must rotate with R1 — replaying the
    // cookie's R0 is exactly the reuse the backend flags as theft.
    vi.advanceTimersByTime(16 * MINUTE);
    const advanced = await refresher.resolve(token);

    expect(fetcher).toHaveBeenCalledTimes(2);
    const secondCallOpts = fetcher.mock.calls[1]?.[1] as {
      body?: { refresh_token?: string };
    };
    expect(secondCallOpts.body?.refresh_token).toBe("R1");
    expect(advanced.accessToken).toBe("A2");
  });

  it.each(["reauth_required", "refresh_reused", "refresh_expired"])(
    "maps the typed %s reason to REAUTH_REQUIRED_ERROR and caches it briefly",
    async (reason) => {
      const fetcher = vi.fn(async () => {
        throw new ApiError(401, undefined, { error: { reason } });
      });
      const refresher = createTokenRefresher(
        fetcher as unknown as RefreshFetcher,
      );

      const token = staleJwt();
      const failed = await refresher.resolve(token);
      expect(failed.error).toBe(REAUTH_REQUIRED_ERROR);

      // Concurrent stragglers inside the cache window get the same terminal
      // answer without hammering /auth/refresh again.
      const straggler = await refresher.resolve(token);
      expect(straggler.error).toBe(REAUTH_REQUIRED_ERROR);
      expect(fetcher).toHaveBeenCalledTimes(1);
    },
  );

  it("keeps transient failures generic and un-cached so the next call retries", async () => {
    const fetcher = vi.fn(async () => {
      throw new Error("ECONNREFUSED");
    });
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const token = staleJwt();
    const first = await refresher.resolve(token);
    expect(first.error).toBe("RefreshAccessTokenError");

    const second = await refresher.resolve(token);
    expect(second.error).toBe("RefreshAccessTokenError");
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("returns a still-valid token untouched without any network", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const fresh = staleJwt({ accessExpiresAt: isoIn(10 * MINUTE) });
    const result = await refresher.resolve(fresh);

    expect(result).toBe(fresh);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("evicts dead chains after the eviction horizon", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const token = staleJwt();
    await refresher.resolve(token);

    // Untouched past the horizon: the chain is gone, so the cookie token is
    // the only lead again (the backend's anchored grace covers this replay).
    vi.advanceTimersByTime(31 * MINUTE);
    await refresher.resolve(token);

    expect(fetcher).toHaveBeenCalledTimes(2);
    const secondCallOpts = fetcher.mock.calls[1]?.[1] as {
      body?: { refresh_token?: string };
    };
    expect(secondCallOpts.body?.refresh_token).toBe("R0");
  });

  it("stamps a generic error when the token has no refresh token at all", async () => {
    const fetcher = pairFetcher();
    const refresher = createTokenRefresher(
      fetcher as unknown as RefreshFetcher,
    );

    const result = await refresher.resolve(
      staleJwt({ refreshToken: undefined }),
    );
    expect(result.error).toBe("RefreshAccessTokenError");
    expect(fetcher).not.toHaveBeenCalled();
  });
});
