# Operations

> Stub - populated during Phase 6 (Polish and harden). The contents below are the planned shape, not implemented detail.

## Deployment targets

- **AWS GovCloud** — Terraform plan under `infra/terraform/aws-govcloud/`.
- **Azure Government** — Terraform plan under `infra/terraform/azure-gov/`.
- No third-party CDNs. All assets served from the deployment's own origin.

## Runtime components

| Component      | Image                                                         | Notes                                                                       |
| -------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------- |
| api            | `infra/docker/api.Dockerfile` (least-privilege user, no sudo) | uvicorn + workers per `WEB_CONCURRENCY`                                     |
| worker         | same image as `api`, different entry                          | Celery worker                                                               |
| web            | `infra/docker/web.Dockerfile`                                 | Next.js standalone output                                                   |
| db             | managed Postgres 16 (RDS / Azure Database for Postgres)       | KMS-encrypted at rest; PITR enabled                                         |
| redis          | managed Redis 7 (ElastiCache / Azure Cache)                   | Multi-AZ                                                                    |
| object storage | S3 + KMS or Azure Blob + KMS                                  | Versioning ON; bucket-level encryption; deny anonymous; tight bucket policy |
| OIDC           | Keycloak (self-hosted) or federated to customer IdP           | Realm export checked into `infra/keycloak/`                                 |
| secrets        | AWS Secrets Manager or Azure Key Vault                        | Bootstrapped via Terraform; rotated quarterly                               |

## Backups

- Postgres: managed point-in-time recovery + nightly snapshot to a separate region.
- Object storage: versioning + cross-region replication on the artifacts bucket.
- Keycloak realm: weekly export to the artifacts bucket.

## Key rotation

- KMS keys rotated annually (automatic on AWS).
- Database credentials rotated quarterly (Secrets Manager rotation lambda).
- API JWT signing key rotated every 90 days; old keys kept hot for the JWT TTL window then archived.

## Monitoring + alerting

- Structured JSON logs to CloudWatch / Log Analytics.
- Metrics: Prometheus exposition from `api`, `worker`, `web`.
- Alerts: latency p95 > 1s; 5xx rate > 1%; queue depth > 1000; redactor failure (page immediately).

## Incident response

Runbook templates under `docs/runbooks/`:

- `incident-response.md`
- `backup-restore.md`
- `key-rotation.md`
- `disaster-recovery.md`
- `redactor-failure.md`

Each runbook lists: signal → triage steps → mitigation → post-incident actions.

## FedRAMP package

- SSP (System Security Plan) draft under `docs/fedramp/ssp.md` (Phase 6).
- SAR (Security Assessment Report) template under `docs/fedramp/sar.md` (Phase 6).
- POA&M (Plan of Action & Milestones) tracker under `docs/fedramp/poam.md` (Phase 6).
