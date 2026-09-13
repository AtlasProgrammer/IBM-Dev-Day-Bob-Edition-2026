from __future__ import annotations

from reportly.export.formatter import ReportFormatter
from reportly.models import ExportJob, ExportResult


class StreamingExporter:
    def __init__(self, formatter: ReportFormatter | None = None, chunk_size: int = 65536) -> None:
        self.formatter = formatter or ReportFormatter()
        self.chunk_size = chunk_size

    def export(self, job: ExportJob) -> ExportResult:
        written = 0
        while True:
            chunk = job.source.read(self.chunk_size)
            if not chunk:
                break
            written += job.destination.write(self.formatter.render_chunk(chunk, job.format))
        job.destination.flush()
        return ExportResult(ok=True, bytes_written=written, report_id=job.report_id)
