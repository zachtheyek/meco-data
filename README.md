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
