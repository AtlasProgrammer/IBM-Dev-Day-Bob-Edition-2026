from dataclasses import dataclass


@dataclass
class Settings:
    env: str = "production"
    service_name: str = "reportly"
    version: str = "2.6.0"
    chunk_size: int = 65536
    migration_in_progress: bool = False
    log_request_headers: bool = True
    redact_secrets: bool = False
    canary_ready_status: int = 503
    atomic_exports: bool = False
    quota_enforced: bool = True
    webhook_fanout: bool = True


settings = Settings()
