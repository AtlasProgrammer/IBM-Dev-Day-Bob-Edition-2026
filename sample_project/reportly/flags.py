from dataclasses import dataclass


@dataclass
class FeatureFlags:
    stream_exports: bool = False
    bind_token_tenant: bool = False
    redact_secrets: bool = False
    canary_ignore_migration: bool = False
    usage_webhooks: bool = True
    audit_exports: bool = True


flags = FeatureFlags()


def drift() -> list[dict[str, str]]:
    items = []
    if not flags.stream_exports:
        items.append(
            {
                "flag": "stream_exports",
                "state": "off",
                "invariant": "Exports MUST use bounded memory regardless of report size.",
            }
        )
    if not flags.bind_token_tenant:
        items.append(
            {
                "flag": "bind_token_tenant",
                "state": "off",
                "invariant": "Tokens MUST be bound to a single tenant.",
            }
        )
    if not flags.redact_secrets:
        items.append(
            {
                "flag": "redact_secrets",
                "state": "off",
                "invariant": "Secrets MUST NOT appear in application logs.",
            }
        )
    if not flags.canary_ignore_migration:
        items.append(
            {
                "flag": "canary_ignore_migration",
                "state": "off",
                "invariant": "/health/ready MUST stay HTTP 200 during online schema migrations.",
            }
        )
    return items
