# Changelog

All notable changes to SHIELD by Kentro v2.0. Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the phase template in AI Prompt §9.

## [Unreleased]

### Opening commit — 2026-05-19

- Repo scaffolded per Master Spec §16 and AI Prompt §8.
- Reference documents relocated to `reference-docs/` with normalized filenames (see DECISIONS.md D-013).
- Dev container configured with `appuser` + passwordless sudo per AI Prompt §3.10–§3.11.
- Docker Compose stack defined for 8 services (db, redis, minio, keycloak, mailhog, api, worker, web).
- Pre-commit hooks and CI workflow seeded per AI Prompt §5 / §8.6.
- Documentation skeleton seeded under `docs/`.
- Seven spec §17 open questions answered in DECISIONS.md (D-003 through D-009); Q5 flipped to full ATT&CK matrix per Eugene's direction.
