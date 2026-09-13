import tempfile
import unittest
from pathlib import Path

from reportly.storage import ObjectStorage


class TestObjectStorage(unittest.TestCase):
    def test_put_and_get_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ObjectStorage(Path(tmp))
            store.put("report.csv", b"id,name\n")
            self.assertEqual(store.get("report.csv"), b"id,name\n")
