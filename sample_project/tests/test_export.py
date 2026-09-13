import io
import unittest

from reportly.export.service import ExportService
from reportly.models import ExportJob


class TestExportService(unittest.TestCase):
    def test_small_csv_export_succeeds(self) -> None:
        source = io.BytesIO(b"id,name\n1,acme\n")
        destination = io.BytesIO()
        job = ExportJob(
            report_id="rpt-small",
            tenant_id="acme",
            format="csv",
            source=source,
            destination=destination,
            request_id="test-small",
        )
        result = ExportService().export(job)
        self.assertTrue(result.ok)
        self.assertEqual(destination.getvalue(), b"id,name\n1,acme\n")

    def test_json_export_minifies_payload(self) -> None:
        source = io.BytesIO(b'{"ok": true, "rows": 1}')
        destination = io.BytesIO()
        job = ExportJob(
            report_id="rpt-json",
            tenant_id="acme",
            format="json",
            source=source,
            destination=destination,
            request_id="test-json",
        )
        result = ExportService().export(job)
        self.assertTrue(result.ok)
        self.assertEqual(destination.getvalue(), b'{"ok":true,"rows":1}')
