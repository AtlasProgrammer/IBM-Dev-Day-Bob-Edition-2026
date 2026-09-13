from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class ObjectStorage:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, name: str, payload: bytes) -> Path:
        target = self.root / name
        target.write_bytes(payload)
        return target

    def put_atomic(self, name: str, payload: bytes) -> Path:
        target = self.root / name
        staging = self.root / f".{name}.{uuid4().hex}.tmp"
        staging.write_bytes(payload)
        staging.replace(target)
        return target

    def get(self, name: str) -> bytes:
        return (self.root / name).read_bytes()
