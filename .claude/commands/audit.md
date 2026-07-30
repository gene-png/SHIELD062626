---
description: Security review of the diff. Ten questions, each answered with a file path and line range or an explicit not-applicable.
argument-hint: [scope, or blank for the working diff]
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(npm audit:*), Bash(npm ls:*), Agent
---

# /audit

## Scope
$ARGUMENTS

If blank, audit the working diff against `main`.

---

Every question below is answered with **a file path and line range, or the exact words
"not applicable, no matching code in this diff"**. A question answered with a judgement
is not answered.

## The ten questions

1. **Row-level security.** Does this diff create or alter a Postgres table, view or
   policy? For each table touched, quote the `ENABLE ROW LEVEL SECURITY` statement and
   every policy. Name any table with RLS enabled but no policy for a command.

2. **Which key.** List every Supabase client instantiation. For each: which key, and does
   the calling path serve a user-facing HTTP request? Quote the import line.

3. **Tenant scoping.** For every query using the service-role key, quote the `WHERE`
   clause and name the column that scopes it to one tenant. If there is none, say so.

4. **Environment reach.** List every new or changed `process.env` reference. For each,
   does the module reach client-side code? Check for `"use client"`, imports from a
   client component, and the absence of `server-only`. Quote the import chain.

5. **Public inlining.** Any new `NEXT_PUBLIC_*` variable? Quote its name and what it
   holds. These are textually inlined into shipped JavaScript at build time and remain in
   already-deployed bundles after the variable is deleted.

6. **Authentication and authorisation.** List every new route handler or server action.
   For each, quote the line that authenticates the caller and the line that authorises
   this specific resource. Absent authorisation is a finding, not an omission.

7. **Dependencies.** List every new npm dependency with version, weekly downloads,
   publish date, and whether it declares install scripts. Flag anything published within
   seven days.

8. **Injection.** Does the diff put a user-controlled value into a SQL string, a shell
   command, a file path, a redirect target, or an outbound URL? Quote each and the
   sanitisation applied.

9. **Swallowed errors.** Any `catch` that neither rethrows nor logs. Quote it.

10. **Rendered model output.** Does the diff render a string that came from a model
    response or a client upload? Quote the render call and say whether it is escaped.

## The model-specific checks

Run these whenever the diff touches a prompt, a model call, or anything reading a
client-supplied document.

**Prompt injection.** Enumerate every tool or function available to a model turn whose
context includes client-supplied content. For a document-analysis turn the correct answer
is zero. If it is not zero, name each tool and what it can reach. Confirm untrusted
content is JSON-encoded rather than concatenated into the prompt, so a quote or a tag
cannot close the boundary.

**Exfiltration through rendering.** Assert that model output cannot emit an image or link
to a host that is not allowlisted. The markdown-image vector has been found and fixed in
ChatGPT plugins, GitHub Copilot and Amp Code. Fix it at the rendering layer plus a CSP
`img-src` and `connect-src`, never at the model layer.

**Cross-client leakage.** Confirm every prompt assembly function takes a tenant
identifier and that retrieval filters by it before the model sees anything. Quote the
filter. Confirm no cache key or embedding is shared across tenants.

## Dependencies, at the right cadence

`npm audit --omit=dev`, and **read it** rather than gating on it. Gating on the full
`npm audit` scores dev-only build tooling like request-path code, so the gate is
permanently red, which is the same as having no gate.

Confirm `ignore-scripts` is set. Every major npm compromise of the last two years, chalk
and debug through Shai-Hulud 2.0 at 796 packages, ran through `preinstall` or
`postinstall` on a machine holding credentials.

## Report

```
| # | Question | Answer | File:lines | Severity |
```

Then: `CLEAN`, or a list of findings ranked by what an attacker gets.

**REFUSE** to report clean on the strength of a green suite, a passing `npm audit`, or a
coverage number. Clean means the ten questions were each answered with a location or an
explicit not-applicable.

## Do not fix anything here

Report only. A security fix made in the same pass as the finding does not get reviewed by
anyone. Findings go to `/spec` and come back through `/tdd`.
