# meco-data — shared data foundation

A small, reproducible pipeline that turns the **Malaysian Election Corpus (MECo)**
into tidy, analysis-ready tables consumed by every project in this collection.

## Source & credit

All underlying data is the **Malaysian Election Corpus (MECo)** by
**Thevesh Thevananthan**, released under **CC0 / public domain**:

- Site & API: <https://electiondata.my>
- Corpus repo: <https://github.com/Thevesh/paper-meco-results>
- Paper: *The Malaysian Election Corpus (MECo): Federal and State-Level Election
  Results from 1955 to 2025*, **Scientific Data 13, 190 (2026)** —
  <https://www.nature.com/articles/s41597-025-06502-7>

This repo only *re-shapes* that corpus. None of the primary data-cleaning credit is ours.

## What it produces

`./.venv/bin/python pipeline.py` reads `raw/*.csv` (mirrored from the corpus) and writes:

| file | grain | notes |
|------|-------|-------|
| `out/ballots.parquet`   | candidate × contest | cleaned, typed, with `seat_type`, `seat_key`, `contest_id` |
| `out/contests.parquet`  | one contest         | winner, runner-up, margin, turnout, electorate |
| `out/seats.parquet`     | one seat            | threaded across delimitations by `(type, state, normalised name)` |
| `out/candidates.parquet`| one candidate       | entity-resolved record + career aggregates |
| `out/lookup_*.parquet`  | —                   | party / coalition entities + succession (lineage) |

### Seat threading caveat

Seat identity is **not stable** across Malaysia's delimitation exercises — numbers are
reassigned and names change (e.g. `P.001` was *Wellesley North → Perlis Utara → Kangar →
Padang Besar*). We thread a seat's history by **normalised name within a state**, which is
honest but name-based, not boundary-based. For true boundary lineage see MECo's electoral
**maps** corpus and the geospatial seat view on electiondata.my.

## Reproduce

```bash
python3 -m venv .venv
./.venv/bin/pip install pandas pyarrow duckdb
./.venv/bin/python pipeline.py     # writes out/
./.venv/bin/python validate.py     # sanity-checks against known results
```

## Refreshing from upstream (automatic)

This repo is the single source of truth the downstream sites build from, and it keeps
itself current. A weekly GitHub Action (`.github/workflows/refresh.yml`, Sundays 20:07
UTC) compares the upstream commit to `.meco-snapshot`; if there's new data it fetches it,
rebuilds `out/`, and commits + pushes automatically. If nothing changed it does nothing.
**lompat** and **undi-wrapped** then rebuild from the new `out/*.parquet` on their own
weekly schedule ~10–30 min later — fully hands-off, end to end.

`.meco-snapshot` records the upstream commit we're built from. The refresh leaves our
manual `raw/corrections.csv` untouched and fails loudly (no push) if `pipeline.py` chokes
on the new data, so a broken upstream surfaces as a failed run rather than bad live data.

To refresh manually (locally, or to force it), it's one line:

```bash
make refresh     # fetch the latest corpus into raw/ + rebuild out/, then commit & push
```
