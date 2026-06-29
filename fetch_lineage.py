#!/usr/bin/env python3
"""
Fetch boundary-based seat lineage from electiondata.my.

For every current seat, electiondata.my can return its history following the *dominant
ancestor* through each redelineation (boundary-based), which is correct where our
name-matching is not — e.g. P.190 Tawau's real ancestor 1986-99 is Semporna, not the
1986 "Tawau". This writes raw/seat_lineage.csv (slug,date,state,seat): for each current
seat, every (date,state,seat) in its ancestor chain. pipeline.py threads seats by it.

Run rarely — only after a new redelineation (lineage doesn't change between elections):
    EDMY_API_KEY=... python fetch_lineage.py
NEVER commit the key. The committed artifact is raw/seat_lineage.csv only.
"""
from __future__ import annotations
import csv, json, os, time, urllib.request
from pathlib import Path

KEY = os.environ.get("EDMY_API_KEY")
if not KEY:
    raise SystemExit("set EDMY_API_KEY (electiondata.my API key) in the environment")
BASE = "https://api.electiondata.my/v1"

HEADERS = {"Authorization": f"Bearer {KEY}", "User-Agent": "meco-data/1.0 (+github.com/zachtheyek/meco-data)", "Accept": "application/json"}

def api(path: str, tries: int = 3):
    for t in range(tries):
        try:
            req = urllib.request.Request(BASE + path, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:  # noqa: BLE001
            if t == tries - 1:
                raise
            time.sleep(1.5 * (t + 1))

seats = api("/seats/dropdown")["seats"]
rows = []
for i, s in enumerate(seats):
    slug = s["slug"]
    try:
        res = api(f"/seats/results?slug={slug}&lineage=true")["results"]
    except Exception as e:  # noqa: BLE001
        print("warn", slug, e); continue
    for r in res:
        if "election_name" in r:  # an election result (vs a boundary-change note)
            rows.append((slug, r["date"], r["state"], r["seat"]))
    if (i + 1) % 100 == 0:
        print(f"  {i + 1}/{len(seats)}")
    time.sleep(0.05)  # be polite — no hard limit but requests are logged

out = Path("raw/seat_lineage.csv")
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["slug", "date", "state", "seat"])
    w.writerows(rows)
print(f"wrote {out}: {len(rows)} ancestor rows across {len(seats)} current seats")
