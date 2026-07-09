/**
 * Client-safe auth error constants. Kept separate from `options.ts` (which
 * imports server-only `next/headers` via the api client) so client components
 * like SessionExpiryGuard can import the signal without dragging server code
 * into the browser bundle.
 */

/**
 * Stamped on the NextAuth session token when the daily forced-reauth ceiling
 * is hit or the refresh token was rotated out (backend reason
 * `reauth_required` / `refresh_reused`). The UI treats it as "sign in again"
 * with friendly copy, distinct from a generic refresh failure.
 */
export const REAUTH_REQUIRED_ERROR = "reauth_required";
