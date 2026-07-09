# Admin guide (Kentro consultant)

> Skeleton — the full consultant guide is still to be written. What follows
> matches the current product; there is no reviewer role and no
> release-to-client gate (DECISIONS D-023).

## What an admin does

The Admin (Kentro consultant) is platform-wide and works across client
tenants (picking the active client via the top-nav switcher):

- Creates client tenants and approves their email domains at
  `/admin/management`; verifies the first registrant as the client's Primary
  POC.
- Watches the intake queue (`/admin/queue`) for new submissions.
- Runs the four services (Tech Debt, ZT, CSF, ATT&CK) and the Risk Register
  through their workspaces: uploads inventories, runs AI drafts, curates the
  results (the deterministic engines compute all scores), and generates the
  versioned deliverables.
- Downloads deliverables (spec §15.5 filenames) to hand off to the client.

A deliberate client-facing release step may return as a Sprint 5 feature; it
does not exist today.
