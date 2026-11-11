# Applying this update

This branch replaces the old placeholder collector with a BoardLib-backed Kilter + Tension logbook sync.

1. Review this branch and merge it when ready.
2. Add the six GitHub Actions secrets listed in README.md.
3. Run the tests locally, then trigger the workflow manually from GitHub Actions.
4. Confirm that the Google Sheet has the expected tabs and records before relying on the weekly schedule.

The old root-level boardlib.py is removed because it shadows the installed BoardLib package and prevents python -m boardlib from importing correctly. Existing Google Sheet rows are retained and migrated as legacy rows on the first sync. The workflow does not store credentials or board logbooks in the repository.
