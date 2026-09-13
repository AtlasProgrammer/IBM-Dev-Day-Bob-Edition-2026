import unittest

from reportly.export.formatter import ReportFormatter


class TestReportFormatter(unittest.TestCase):
    def test_csv_passthrough(self) -> None:
        self.assertEqual(ReportFormatter().render(b"a,b\n", "csv"), b"a,b\n")

    def test_chunk_passthrough(self) -> None:
        self.assertEqual(ReportFormatter().render_chunk(b"chunk", "csv"), b"chunk")
