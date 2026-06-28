import pandas as pd
b=pd.read_parquet("out/ballots.parquet")
succ=pd.read_parquet("out/lookup_party_succession.parquet")
# canonical party via "replace" successions (renames): map predecessor->successor transitively
replace=succ[succ.type=="replace"][["predecessor_uid","successor_uid"]]
canon={}
def find(u):
    seen=set()
    while u in dict(zip(replace.predecessor_uid,replace.successor_uid)) and u not in seen:
        seen.add(u); u=dict(zip(replace.predecessor_uid,replace.successor_uid))[u]
    return u
m=dict(zip(replace.predecessor_uid,replace.successor_uid))
def canonical(u):
    seen=set()
    while u in m and u not in seen:
        seen.add(u); u=m[u]
    return u
b=b.dropna(subset=["candidate_uid","party_uid"]).copy()
b["pcanon"]=b["party_uid"].map(canonical)
b=b.sort_values(["candidate_uid","date"])
# per candidate, sequence of canonical parties across contests
def switches(g):
    seq=g["pcanon"].tolist()
    distinct_parties=g["pcanon"].nunique()
    sw=sum(1 for i in range(1,len(seq)) if seq[i]!=seq[i-1])
    return pd.Series({"n_contests":len(g),"distinct_parties":distinct_parties,"switches":sw})
agg=b.groupby("candidate_uid").apply(switches).reset_index()
lk=pd.read_parquet("out/candidates.parquet")[["candidate_uid","name"]]
agg=agg.merge(lk,on="candidate_uid",how="left")
print("=== Top 12 by switches (canonicalised, renames excluded) ===")
print(agg.sort_values(["switches","distinct_parties"],ascending=False).head(12)[["name","n_contests","distinct_parties","switches"]].to_string(index=False))
print("\n=== How many candidates ever switched? ===")
print(f"{(agg.switches>0).sum()} of {len(agg)} multi-contest candidates" )
