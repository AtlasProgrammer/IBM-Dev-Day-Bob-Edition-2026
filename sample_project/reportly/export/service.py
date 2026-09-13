from __future__ import annotations

from dataclasses import dataclass

from reportly.export.formatter import ReportFormatter
from reportly.flags import flags
from reportly.models import ExportJob, ExportResult
from reportly.observability import get_logger


@dataclass
class ExportOptions:
    chunk_size: int = 65536
    atomic: bool = True


class ExportService:
    def __init__(self, formatter: ReportFormatter | None = None, options: ExportOptions | None = None) -> None:
        self.formatter = formatter or ReportFormatter()
        self.options = options or ExportOptions()
        self.log = get_logger("reportly.export")

    def export(self, job: ExportJob) -> ExportResult:
        self.log.info(
            "export.started",
            rid=job.request_id,
            report=job.report_id,
            tenant=job.tenant_id,
        )
        try:
            if flags.stream_exports:
                written = 0
                while True:
                    chunk = job.source.read(self.options.chunk_size)
                    if not chunk:
                        break
                    written += job.destination.write(self.formatter.render_chunk(chunk, job.format))
            else:
                raw = job.source.read()
                rendered = self.formatter.render(raw, job.format)
                written = job.destination.write(rendered)
            job.destination.flush()
            self.log.info("export.completed", rid=job.request_id, report=job.report_id, bytes=written)
            return ExportResult(ok=True, bytes_written=written, report_id=job.report_id)
        except MemoryError as exc:
            self.log.error(
                "export.failed",
                rid=job.request_id,
                report=job.report_id,
                error="MemoryError",
                detail=str(exc),
            )
            raise
        except Exception as exc:
            self.log.error(
                "export.failed",
                rid=job.request_id,
                report=job.report_id,
                error=type(exc).__name__,
                detail=str(exc),
            )
            raise
