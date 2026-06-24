import duckdb, re, unicodedata
con=duckdb.connect(); B="raw/consol_ballots.csv"
def q(s): return con.execute(s).fetchdf()
# pull distinct (election,date,state,seat) federal contests
df=q(f"""select distinct election,date,state,seat from '{B}' where seat like 'P.%' and election like 'GE-%'""")
def norm(seat):
    name=re.sub(r'^P\.\d+\s+','',seat)
    name=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower().strip()
    # common spelling unifications
    repl={'datoh':'datuk','datok':'datuk','bahru':'baru','baharu':'baru','ulu':'hulu'}
    toks=[repl.get(t,t) for t in re.split(r'\s+',name)]
    return ' '.join(toks)
df['key']=df['state']+'|'+df['seat'].map(norm)
# how many distinct GEs does each current (GE-15) seat thread back through?
ge15=set(df[df.election=='GE-15']['key'])
sub=df[df.key.isin(ge15)]
g=sub.groupby('key')['election'].nunique()
import numpy as np
print("Current federal seats (GE-15):", len(ge15))
print("Threaded-back GE count distribution (how many GEs each current seat appears in by name):")
print(g.value_counts().sort_index().to_string())
print(f"\nMean GEs per current seat: {g.mean():.1f}  (max possible 16)")
print(f"Seats whose name reaches back to 1959 or earlier (>=14 GEs): {(g>=14).sum()}")
print(f"Seats appearing only in GE-15 (no name history): {(g==1).sum()}")
# show a few that thread deep and a few shallow
print("\nDeep threads (sample):")
for k in g[g>=15].index[:5]:
    yrs=sorted(sub[sub.key==k]['date'].astype(str).str[:4]); print(" ", k, "->", yrs[0],"to",yrs[-1], f"({len(yrs)} GEs)")
print("Shallow (GE-15 only) sample:")
for k in g[g==1].index[:8]: print("  ", k)
