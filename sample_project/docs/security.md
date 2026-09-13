# Reportly security contract

## Identity

Bearer tokens in `reportly.auth.REGISTRY` are the only production identities. Each token MUST map to exactly one `tenant_id`.

`X-Tenant-Id` is a caller claim. If it disagrees with the token tenant, the API MUST return HTTP 403 `tenant_mismatch`.

## Logging

`Authorization`, `Cookie`, `X-Api-Key`, and cloud session tokens MUST be redacted before they reach a logger or log shipper.

## Tenancy

An Acme identity MUST NOT read or export Northwind objects. Audit events MUST record `cross_tenant` when the claim and the token disagree so paging does not depend on an engineer grepping access logs.

## Release

Online migrations MUST NOT fail `/health/ready`. Failed readiness is a deploy rollback, not a migration signal.
