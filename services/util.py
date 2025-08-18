import io
import csv
from datetime import datetime
from typing import Any

def parse_date(s: str | None):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def validate_date_range(start, end, max_days: int = 365 * 3):
    if not start or not end:
        return False, "start_date and end_date (YYYY-MM-DD) are required"
    if start > end:
        return False, "start_date must be <= end_date"
    if (end - start).days > max_days:
        return False, f"Date range too long; must be <= {max_days} days"
    return True, "ok"

def to_csv_bytes(records: list[dict]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "query_id",
            "location_name",
            "country",
            "lat",
            "lon",
            "start_date",
            "end_date",
            "query_date",
            "t_min",
            "t_max",
            "t_mean",
        ]
    )
    for r in records:
        loc: dict[str, Any] = r.get("location") or {}
        for obs in r.get("observations", []) or []:
            writer.writerow(
                [
                    r.get("id"),
                    loc.get("name"),
                    loc.get("country"),
                    loc.get("latitude"),
                    loc.get("longitude"),
                    r.get("start_date"),
                    r.get("end_date"),
                    obs.get("query_date"),
                    obs.get("t_min"),
                    obs.get("t_max"),
                    obs.get("t_mean"),
                ]
            )
    return out.getvalue().encode("utf-8")
