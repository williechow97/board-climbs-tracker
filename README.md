# Board Climbs Tracker

Weekly, idempotent Kilter Board + Tension Board logbook collection with performance-focused reporting in Google Sheets.

## What changed

- Replaces the placeholder API with maintained [BoardLib](https://github.com/lemeryfertitta/BoardLib) integration (0.16.0).
- Uses the current Kilter app integration and the Aurora-based Tension integration. Tension's shared climb database is synchronized before its logbook is read.
- Fixes the workflow script path and adds a Python entry point.
- Uses Google Sheets as the durable historical store. Each run merges records by a deterministic fingerprint to avoid re-adding identical entries.
- Rebuilds overview, weekly progression, grade pyramid, and angle reports every run.
- Preserves old three-column date/route_name/grade rows as legacy rows during migration.
- Fails the GitHub Actions job on collection or upload errors.

## Google Sheet tabs

| Tab | Purpose |
|---|---|
| Climbs | Full source logbook: board, angle, climb, date, grades, attempts, send/repeat/benchmark flags, comment |
| Overview | Entries, sends, unique climbs, attempts, attempts per send, flashes/rate, highest sent V grade, climbing days, split by board |
| Progression | Weekly sends, attempts, attempts per send, flash rate, unique climbs, split by board |
| Grade Pyramid | Sends by displayed grade and share of all sends |
| Angles | Sends, attempts, attempts per send, flash rate, unique climbs by board angle |

## Required GitHub Actions secrets

In Settings → Secrets and variables → Actions, add:

| Secret | Value |
|---|---|
| KILTER_USERNAME | Email used to sign in to the current Kilter app |
| KILTER_PASSWORD | Kilter app password |
| TENSION_USERNAME | Tension Board account username |
| TENSION_PASSWORD | Tension Board account password |
| SHEET_ID | Spreadsheet ID from the Google Sheets URL |
| GOOGLE_SERVICE_ACCOUNT_JSON | Entire JSON key file contents for a Google service account |

### Google Sheets service account

1. Enable the Google Sheets API in a Google Cloud project.
2. Create a service account and generate a JSON key.
3. Store the complete JSON key contents in GOOGLE_SERVICE_ACCOUNT_JSON.
4. Share the spreadsheet with the service account's client_email as Editor.
5. Put the spreadsheet ID in SHEET_ID.

Do not commit credentials, passwords, exported logbooks, or database files. Do not paste passwords or service-account keys into chat or issues. The service account only needs access to the spreadsheet.

## Schedule and local use

GitHub Actions runs every Monday at 17:00 UTC (09:00 Pacific Standard Time / 10:00 Pacific Daylight Time). You can also run it manually from Actions → Weekly Climbing Logbook Sync → Run workflow.

Python 3.10+ is recommended:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
python tracker.py
```

For local Google authentication, set GOOGLE_APPLICATION_CREDENTIALS=credentials.json in .env. The GitHub workflow uses the JSON secret.

## Metric definitions and caveats

- A send is a BoardLib row whose is_ascent field is true.
- A flash is a send recorded with tries == 1. Flash rate is flashes divided by sends.
- Average attempts per send uses sent rows only; total logged attempts sum tries across all returned rows.
- Unique climb counts use board + climb name + angle.
- Grade pyramid and highest grade use displayed_grade, falling back to logged_grade. Numeric ordering supports Hueco V grades; other systems remain labels.
- Current Kilter app history begins around its March 2026 migration. Older Aurora-era Kilter history may need to be exported through Kilter support and migrated separately.
- Treat small weekly samples cautiously. Compare rolling multi-week trends and similar angles/grades rather than overinterpreting one week.

## Troubleshooting

- Authentication failure: verify credentials; Kilter username is the account email.
- Tension logbook failure: verify both Tension credentials and allow BoardLib to synchronize the shared climb database.
- Google API permission error: enable Sheets API and share the spreadsheet with the service account email as Editor.
- No data returned: inspect workflow logs and the board app logbook. An empty export is not a confirmed zero-climb week.

## Dependencies

- [BoardLib](https://github.com/lemeryfertitta/BoardLib)
- Google Sheets API
