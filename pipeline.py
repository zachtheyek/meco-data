"""
MECo shared data foundation
===========================
Cleans the Malaysian Election Corpus (paper-meco-results) into a small set of
tidy, analysis-ready tables that every downstream project consumes.

Source : https://github.com/Thevesh/paper-meco-results  (CC0 / public domain)
Corpus : Thevesh Thevananthan, "The Malaysian Election Corpus (MECo)",
         Scientific Data 13, 190 (2026).  https://electiondata.my

Run:  ./.venv/bin/python pipeline.py
Out:  out/*.parquet  (+ a few .csv for eyeballing)
"""
from __future__ import annotations
import re, unicodedata, json
from pathlib import Path
import pandas as pd

RAW = Path("raw")
OUT = Path("out")
OUT.mkdir(exist_ok=True)

# --- spelling unifications that recur across delimitations -------------------
_SPELL = {
    "datoh": "datuk", "datok": "datuk",
    "bahru": "baru", "baharu": "baru",
    "ulu": "hulu",
    "hilor": "hilir",
}

def norm_name(seat: str) -> str:
    """Bare, accent-/spelling-normalised seat name (no P.### / N.## prefix)."""
    name = re.sub(r"^[PN]\.\d+\s+", "", seat)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.lower().strip()
    toks = [_SPELL.get(t, t) for t in re.split(r"\s+", name) if t]
    return " ".join(toks)


def load_ballots() -> pd.DataFrame:
    b = pd.read_csv(RAW / "consol_ballots.csv", dtype=str)
    b["votes"] = pd.to_numeric(b["votes"], errors="coerce").fillna(0).astype(int)
    b["votes_perc"] = pd.to_numeric(b["votes_perc"], errors="coerce")
    b["rank"] = pd.to_numeric(b["rank"], errors="coerce").astype("Int64")
    b["age"] = pd.to_numeric(b["age"], errors="coerce")
    b.loc[b["age"] < 0, "age"] = pd.NA          # -1 sentinel = unknown
    b["seat_type"] = b["seat"].str[0].map({"P": "federal", "N": "state"})
    b["seat_no"] = b["seat"].str.extract(r"^[PN]\.(\d+)")
    b["seat_name"] = b["seat"].str.replace(r"^[PN]\.\d+\s+", "", regex=True)
    b["seat_key"] = b["seat_type"] + "|" + b["state"] + "|" + b["seat"].map(norm_name)
    b["contest_id"] = b["date"] + "|" + b["state"] + "|" + b["seat"]
    b["year"] = b["date"].str[:4].astype(int)
    return b


def build_contests(b: pd.DataFrame) -> pd.DataFrame:
    """One row per contest with winner / runner-up / margin, joined to stats."""
    stats = pd.read_csv(RAW / "consol_stats.csv", dtype=str)
    for c in ["voters_total", "ballots_issued", "votes_rejected", "votes_valid",
              "majority", "n_candidates", "ballots_not_returned"]:
        stats[c] = pd.to_numeric(stats[c], errors="coerce")
    for c in ["voter_turnout", "majority_perc", "votes_rejected_perc"]:
        stats[c] = pd.to_numeric(stats[c], errors="coerce")
    stats["contest_id"] = stats["date"] + "|" + stats["state"] + "|" + stats["seat"]

    b = b.sort_values(["contest_id", "rank"])
    win = b[b["rank"] == 1].drop_duplicates("contest_id")
    run = b[b["rank"] == 2].drop_duplicates("contest_id")

    meta_cols = ["contest_id", "date", "election", "state", "seat",
                 "seat_type", "seat_no", "seat_name", "seat_key", "year"]
    c = b[meta_cols].drop_duplicates("contest_id").copy()
    c = c.merge(win[["contest_id", "candidate_uid", "name", "party_uid", "party",
                     "coalition_uid", "coalition", "votes", "votes_perc", "result"]]
                .rename(columns=lambda x: x if x == "contest_id" else "win_" + x),
                on="contest_id", how="left")
    c = c.merge(run[["contest_id", "party_uid", "party", "coalition_uid",
                     "coalition", "votes", "votes_perc"]]
                .rename(columns=lambda x: x if x == "contest_id" else "run_" + x),
                on="contest_id", how="left")
    c = c.merge(stats[["contest_id", "voters_total", "votes_valid", "majority",
                       "n_candidates", "voter_turnout", "majority_perc"]],
                on="contest_id", how="left")
    # margin in percentage points of valid votes (uncontested -> NA)
    c["margin_perc"] = c["win_votes_perc"] - c["run_votes_perc"]
    c["uncontested"] = c["win_result"].eq("won_uncontested")
    return c


def build_seats(c: pd.DataFrame) -> pd.DataFrame:
    """Seat dimension threaded by (type,state,normalised name)."""
    rows = []
    for key, g in c.groupby("seat_key"):
        g = g.sort_values("date")
        latest = g.iloc[-1]
        rows.append({
            "seat_key": key,
            "seat_type": latest["seat_type"],
            "state": latest["state"],
            "current_name": latest["seat_name"],
            "current_seat": latest["seat"],
            "names": " / ".join(sorted(g["seat_name"].unique())),
            "n_names": g["seat_name"].nunique(),
            "first_year": int(g["year"].min()),
            "last_year": int(g["year"].max()),
            "n_contests": len(g),
            "still_current": bool(latest["election"] in ("GE-15", "SE-15")),
        })
    return pd.DataFrame(rows)


def build_candidates(b: pd.DataFrame) -> pd.DataFrame:
    lk = pd.read_csv(RAW / "lookup_candidate.csv", dtype=str)
    career = (b.groupby("candidate_uid")
                .agg(n_contests=("contest_id", "nunique"),
                     n_wins=("result", lambda s: s.isin(["won", "won_uncontested"]).sum()),
                     first_year=("year", "min"),
                     last_year=("year", "max"),
                     parties=("party_uid", lambda s: s.dropna().nunique()),
                     total_votes=("votes", "sum"))
                .reset_index())
    return lk.merge(career, on="candidate_uid", how="left")


def main():
    b = load_ballots()
    c = build_contests(b)
    seats = build_seats(c)
    cands = build_candidates(b)

    # copy lookups straight through
    for name in ["lookup_party", "lookup_coalition",
                 "lookup_party_succession", "lookup_coalition_succession",
                 "lookup_dates", "lookup_prk"]:
        pd.read_csv(RAW / f"{name}.csv", dtype=str).to_parquet(OUT / f"{name}.parquet")

    # Boundary-based seat lineage (electiondata.my, via fetch_lineage.py). This is the
    # CORRECT cross-delimitation threading: per current seat, the (date,state,seat) of every
    # election in its dominant-ancestor chain. It is one-to-MANY (a split seat is a shared
    # ancestor of several modern seats — e.g. 1959 Damansara → 11 modern KL/Selangor seats),
    # so it is a per-seat lookup, NOT a per-contest id. Seat-centric projects (undi-wrapped)
    # build each seat's history by joining this to contests on (date,state,seat).
    lin_path = RAW / "seat_lineage.csv"
    if lin_path.exists():
        pd.read_csv(lin_path, dtype=str).to_parquet(OUT / "seat_lineage.parquet")
        print(f"seat lineage: {sum(1 for _ in open(lin_path)) - 1:>6,} ancestor rows (boundary-based)")
    else:
        print("seat lineage: (none — run `EDMY_API_KEY=... python fetch_lineage.py`)")

    b.to_parquet(OUT / "ballots.parquet")
    c.to_parquet(OUT / "contests.parquet")
    seats.to_parquet(OUT / "seats.parquet")
    cands.to_parquet(OUT / "candidates.parquet")
    # human-eyeball CSVs
    c.to_csv(OUT / "contests.csv", index=False)
    seats.to_csv(OUT / "seats.csv", index=False)

    print(f"ballots   : {len(b):>7,} rows")
    print(f"contests  : {len(c):>7,} rows  ({c.seat_type.eq('federal').sum():,} federal, "
          f"{c.seat_type.eq('state').sum():,} state)")
    print(f"seats      : {len(seats):>7,} threaded seats "
          f"({seats.seat_type.eq('federal').sum()} federal, {seats.seat_type.eq('state').sum()} state)")
    print(f"candidates : {len(cands):>7,} rows")


if __name__ == "__main__":
    main()
