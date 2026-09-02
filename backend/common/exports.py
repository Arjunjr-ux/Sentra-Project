"""Excel export helper shared by the users / roles / audit-logs list endpoints
(SENTRA_BUILD_SPEC.md §4): openpyxl in write-only mode, the caller's already
filtered queryset iterated with ``.iterator(chunk_size=500)``, hard-capped at
10,000 rows, returned as a proper ``.xlsx`` attachment."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from openpyxl import Workbook

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ITER_CHUNK_SIZE = 500


def export_row_cap() -> int:
    return int(getattr(settings, "EXPORT_MAX_ROWS", 10_000))


def build_xlsx_response(
    *,
    filename: str,
    headers: list[str],
    queryset,
    row_builder: Callable[[object], Iterable],
) -> tuple[HttpResponse, int]:
    """Return ``(response, row_count)``. ``row_count`` is what actually landed in
    the sheet (post-filter, post-cap) so the caller can record it in the audit
    trail."""

    cap = export_row_cap()
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet()
    sheet.append(headers)

    written = 0
    for obj in queryset.iterator(chunk_size=ITER_CHUNK_SIZE):
        if written >= cap:
            break
        sheet.append([_cell(value) for value in row_builder(obj)])
        written += 1

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response, written


def _cell(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
