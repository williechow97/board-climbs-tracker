"""Weekly Kilter + Tension Board logbook sync and climbing analytics."""
from __future__ import annotations
import csv, hashlib, json, logging, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LOG = logging.getLogger("climb-tracker")
BOARD_FIELDS = ["board", "angle", "climb_name", "date", "logged_grade", "displayed_grade",
                "is_benchmark", "tries", "is_mirror", "sessions_count", "tries_total",
                "is_repeat", "is_ascent", "comment"]
FIELDS = ["record_id", *BOARD_FIELDS]
TABS = ["Climbs", "Overview", "Progression", "Grade Pyramid", "Angles"]
GRADE_RE = re.compile(r"^V(\\d+)([+-]?)$", re.I)


def as_bool(value: Any) -> bool | str:
    if value in (None, ""):
        return ""
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    row = {k: raw.get(k, "") for k in BOARD_FIELDS}
    row["board"] = str(row["board"] or "").strip().lower()
    row["climb_name"] = str(row["climb_name"] or "").strip()
    row["date"] = str(row["date"] or "").strip()
    for k in ("is_benchmark", "is_mirror", "is_repeat", "is_ascent"):
        row[k] = as_bool(row[k])
    for k in ("angle", "tries", "sessions_count", "tries_total"):
        try:
            row[k] = int(float(row[k])) if row[k] not in (None, "") else ""
        except (TypeError, ValueError):
            row[k] = ""
    for k in ("logged_grade", "displayed_grade", "comment"):
        row[k] = str(row[k] or "").strip()
    fingerprint = json.dumps({k: str(row[k]) for k in BOARD_FIELDS}, sort_keys=True, ensure_ascii=False)
    row["record_id"] = hashlib.sha256(fingerprint.encode()).hexdigest()[:20]
    return row


def read_logbook(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [normalize(r) for r in csv.DictReader(f)]


def parse_day(value: Any) -> date | None:
    if not value:
        return None
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    return None


def grade_key(grade: Any) -> tuple[int, int] | None:
    m = GRADE_RE.match(str(grade or "").strip())
    if not m:
        return None
    return int(m.group(1)), {"-": -1, "": 0, "+": 1}[m.group(2)]


def mean(values: list[float]) -> float | str:
    return round(sum(values) / len(values), 2) if values else ""


def rate(n: int, d: int) -> float | str:
    return round(n / d, 4) if d else ""


def analytics(records: list[dict[str, Any]]) -> dict[str, list[list[Any]]]:
    sends = [r for r in records if r["is_ascent"] is True]
    def subset(board: str) -> list[dict[str, Any]]:
        return records if board == "all" else [r for r in records if r["board"] == board]
    overview = [["Metric", "All boards", "Kilter", "Tension"]]
    metrics = [
        ("Logged entries", lambda rs: len(rs)),
        ("Sends", lambda rs: sum(r["is_ascent"] is True for r in rs)),
        ("Unique climbs sent", lambda rs: len({(r["board"], r["climb_name"], r["angle"]) for r in rs if r["is_ascent"] is True})),
        ("Total logged attempts", lambda rs: sum(int(r["tries"] or 0) for r in rs)),
        ("Average attempts per send", lambda rs: mean([float(r["tries"]) for r in rs if r["is_ascent"] is True and r["tries"] != ""])),
        ("Flash sends", lambda rs: sum(r["is_ascent"] is True and r["tries"] == 1 for r in rs)),
        ("Flash rate", lambda rs: rate(sum(r["is_ascent"] is True and r["tries"] == 1 for r in rs), sum(r["is_ascent"] is True for r in rs))),
        ("Highest sent V grade", lambda rs: max((str(r["displayed_grade"] or r["logged_grade"]) for r in rs if r["is_ascent"] is True and grade_key(r["displayed_grade"] or r["logged_grade"])), key=lambda g: grade_key(g) or (-1, 0), default="")),
        ("Climbing days", lambda rs: len({parse_day(r["date"]) for r in rs if parse_day(r["date"])})),
    ]
    for label, fn in metrics:
        overview.append([label, *(fn(subset(b)) for b in ("all", "kilter", "tension"))])

    weeks: dict[tuple[date, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        d = parse_day(r["date"])
        if d:
            weeks[(d - timedelta(days=d.weekday()), r["board"] or "unknown")].append(r)
    progression = [["Week starting", "Board", "Sends", "Attempts", "Avg attempts per send", "Flash rate", "Unique climbs sent"]]
    for (week, board), rows in sorted(weeks.items()):
        ss = [r for r in rows if r["is_ascent"] is True]
        tries = [float(r["tries"]) for r in ss if r["tries"] != ""]
        progression.append([week.isoformat(), board, len(ss), sum(int(r["tries"] or 0) for r in rows),
                            mean(tries), rate(sum(r["tries"] == 1 for r in ss), len(ss)),
                            len({(r["climb_name"], r["angle"]) for r in ss})])

    grade_counts: Counter[str] = Counter()
    for r in sends:
        g = str(r["displayed_grade"] or r["logged_grade"] or "").strip()
        if g:
            grade_counts[g] += 1
    pyramid = [["Grade", "Sends", "Share of sends"]]
    for g, count in sorted(grade_counts.items(), key=lambda x: grade_key(x[0]) or (-1, 0)):
        pyramid.append([g, count, rate(count, len(sends))])

    angle_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if r["angle"] != "":
            angle_groups[(r["board"], str(r["angle"]))].append(r)
    angles = [["Board", "Angle", "Sends", "Attempts", "Avg attempts per send", "Flash rate", "Unique climbs sent"]]
    for (board, angle), rows in sorted(angle_groups.items()):
        ss = [r for r in rows if r["is_ascent"] is True]
        angles.append([board, angle, len(ss), sum(int(r["tries"] or 0) for r in rows),
                       mean([float(r["tries"]) for r in ss if r["tries"] != ""]),
                       rate(sum(r["tries"] == 1 for r in ss), len(ss)),
                       len({r["climb_name"] for r in ss})])
    return {"Overview": overview, "Progression": progression, "Grade Pyramid": pyramid, "Angles": angles}


def collect(workdir: Path) -> list[dict[str, Any]]:
    ku, tu = os.getenv("KILTER_USERNAME"), os.getenv("TENSION_USERNAME")
    if not ku or not os.getenv("KILTER_PASSWORD"):
        raise RuntimeError("Set KILTER_USERNAME and KILTER_PASSWORD.")
    if not tu or not os.getenv("TENSION_PASSWORD"):
        raise RuntimeError("Set TENSION_USERNAME and TENSION_PASSWORD.")
    def run(*args: str) -> None:
        LOG.info("BoardLib: %s", " ".join(args[:2]))
        subprocess.run([sys.executable, "-m", "boardlib", *args], check=True, timeout=900)
    kilter_csv, tension_csv = workdir / "kilter.csv", workdir / "tension.csv"
    tension_db = workdir / "tension.db"
    run("logbook", "kilter", "--username", ku, "--output", str(kilter_csv))
    run("database", "tension", str(tension_db), "--username", tu)
    run("logbook", "tension", "--username", tu, "--output", str(tension_csv), "--database-path", str(tension_db))
    return read_logbook(kilter_csv) + read_logbook(tension_csv)


def existing_records(values: list[list[Any]]) -> list[dict[str, Any]]:
    if not values:
        return []
    header = [str(v).strip().lower() for v in values[0]]
    if "record_id" in header:
        indexes = {name: i for i, name in enumerate(header)}
        result = []
        for line in values[1:]:
            raw = {k: line[indexes[k]] if k in indexes and indexes[k] < len(line) else "" for k in BOARD_FIELDS}
            row = normalize(raw)
            if indexes["record_id"] < len(line) and line[indexes["record_id"]]:
                row["record_id"] = str(line[indexes["record_id"]])
            result.append(row)
        return result
    known_headers = {"date", "route_name", "climb_name", "name", "grade", "displayed_grade"}
    has_header = any(cell in known_headers for cell in header)
    def col(names: tuple[str, ...], fallback: int) -> int:
        return next((header.index(n) for n in names if n in header), fallback)
    di, ni, gi = col(("date",), 0), col(("route_name", "climb_name", "name"), 1), col(("grade", "displayed_grade"), 2)
    result = []
    for line in values[1:] if has_header else values:
        if line:
            result.append(normalize({"board": "legacy", "date": line[di] if di < len(line) else "",
                                     "climb_name": line[ni] if ni < len(line) else "",
                                     "displayed_grade": line[gi] if gi < len(line) else ""}))
    return result


def sheets_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    cred_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if secret:
        creds = Credentials.from_service_account_info(json.loads(secret), scopes=scopes)
    elif cred_file and Path(cred_file).is_file():
        creds = Credentials.from_service_account_file(cred_file, scopes=scopes)
    else:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS.")
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def sync_sheet(new_rows: list[dict[str, Any]]) -> tuple[int, int]:
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("SHEET_ID is missing.")
    service = sheets_service()
    meta = service.spreadsheets().get(spreadsheetId=sheet_id, fields="sheets.properties.title").execute()
    present = {s["properties"]["title"] for s in meta.get("sheets", [])}
    additions = [{"addSheet": {"properties": {"title": t}}} for t in TABS if t not in present]
    if additions:
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": additions}).execute()
    response = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Climbs!A:O").execute()
    old = existing_records(response.get("values", []))
    merged = {r["record_id"]: r for r in old}
    before = len(merged)
    for r in new_rows:
        merged[r["record_id"]] = r
    rows = sorted(merged.values(), key=lambda r: (r["date"], r["board"], r["climb_name"], str(r["angle"])))
    climbs = [FIELDS] + [[r.get(k, "") for k in FIELDS] for r in rows]
    outputs = {"Climbs": climbs, **analytics(rows)}
    for tab, values in outputs.items():
        service.spreadsheets().values().update(spreadsheetId=sheet_id, range=f"'{tab}'!A1",
            valueInputOption="RAW", body={"majorDimension": "ROWS", "values": values}).execute()
    return len(merged) - before, len(rows)


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s %(levelname)s %(message)s")
    workdir = Path(os.getenv("WORKDIR", ".tracker-work"))
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        added, total = sync_sheet(collect(workdir))
        LOG.info("Sync complete: %d new rows; %d total rows.", added, total)
        return 0
    except Exception:
        LOG.exception("Tracker failed")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
