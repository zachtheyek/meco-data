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
| `out/seats.parquet`     | one seat            | name-threaded dimension (legacy; prefer `seat_lineage` for history) |
| `out/candidates.parquet`| one candidate       | entity-resolved record + career aggregates |
| `out/seat_lineage.parquet` | current seat × ancestor | **boundary-based** lineage: per current seat, every `(date,state,seat)` in its dominant-ancestor chain |
| `out/lookup_*.parquet`  | —                   | party / coalition entities + succession (lineage) |

### Seat lineage (boundary-based) — use this to thread a seat's history

Seat identity is **not stable** across Malaysia's delimitations: numbers are reassigned,
names change, and — critically — a seat can **keep its name while its boundaries are wholly
replaced** (e.g. pre-2003 *P.190 Tawau* has **zero** overlap with today's Tawau; its real
ancestor is the old *Semporna*). So name-matching is wrong, and the failure is invisible to
name checks. `out/seat_lineage.parquet` is the correct source: for each current seat it
lists every election in its **dominant-ancestor** chain (from electiondata.my). A split
ancestor is shared by several modern seats (1959 *Damansara* → 11 modern KL/Selangor seats),
so it's a **one-to-many lookup, not a per-contest id** — join it to `contests` on
`(date,state,seat)` and group by `slug` to build each seat's true history. (Seat-centric
projects like undi-wrapped do exactly this.)

**Refreshing the lineage** (only needed after a *new redelineation* — it doesn't change
between elections, so it's deliberately not in the weekly CI):

```bash
EDMY_API_KEY=<your electiondata.my key> python fetch_lineage.py   # writes raw/seat_lineage.csv
python pipeline.py                                                 # -> out/seat_lineage.parquet
```

The key is **never committed** — it's read from the environment for this one manual fetch;
only the resulting `raw/seat_lineage.csv` is committed. Routine (weekly) refreshes reuse that
committed snapshot and need no key; a new election under unchanged boundaries is picked up
automatically by name downstream.

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
