#!/usr/bin/env python3
"""
Refresh raw/ from the upstream Malaysian Election Corpus.

Downloads the consolidated source tables from Thevesh/paper-meco-results (CC0) into
raw/, then records the upstream commit in .meco-snapshot so the weekly check knows
whether we're current. Run `python pipeline.py` afterwards (or just `make refresh`).

corrections.csv is OURS (manual fixes) and is never overwritten.
"""
from __future__ import annotations
import json, urllib.request
from pathlib import Path

REPO, BRANCH = "Thevesh/paper-meco-results", "main"
FILES = [
    "consol_ballots", "consol_stats", "lookup_candidate", "lookup_coalition",
    "lookup_coalition_succession", "lookup_dates", "lookup_party",
    "lookup_party_succession", "lookup_prk",
]
RAW = Path("raw"); RAW.mkdir(exist_ok=True)
base = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data"

for f in FILES:
    url = f"{base}/{f}.csv"
    print("fetch", url)
    urllib.request.urlretrieve(url, RAW / f"{f}.csv")

try:
    sha = json.load(urllib.request.urlopen(
        f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"))["sha"]
    Path(".meco-snapshot").write_text(sha + "\n")
    print("recorded upstream snapshot:", sha)
except Exception as e:  # noqa: BLE001
    print("warn: could not record snapshot sha:", e)

print("done — now run `python pipeline.py` to rebuild out/ (or use `make refresh`).")
