import pandas as pd
c=pd.read_parquet("out/contests.parquet")
cand=pd.read_parquet("out/candidates.parquet")
# 1. GE-15 federal winners by coalition (PH should lead, then PN, BN)
g15=c[(c.election=="GE-15")&(c.seat_type=="federal")]
print("GE-15 federal seats won by coalition:")
print(g15.win_coalition.value_counts().to_string())
print(f"  total federal seats GE-15: {len(g15)} (expect 222)")
# 2. GE-14 federal: PH won govt (first time BN lost)
g14=c[(c.election=="GE-14")&(c.seat_type=="federal")]
print("\nGE-14 federal top coalitions:")
print(g14.win_coalition.value_counts().head(4).to_string())
# 3. Lim Kit Siang - most contests
print("\nMost-contested candidates:")
print(cand.sort_values("n_contests",ascending=False)[["name","n_contests","n_wins","first_year","last_year"]].head(5).to_string(index=False))
# 4. closest-ever federal race (smallest nonzero margin)
cc=c[(c.seat_type=="federal")&(~c.uncontested)&(c.margin_perc.notna())]
print("\nClosest-ever federal contests (margin pp):")
print(cc.nsmallest(5,"margin_perc")[["date","seat","win_party","run_party","margin_perc"]].to_string(index=False))
# 5. uncontested counts over time (federal)
print("\nFederal uncontested by decade:")
fc=c[c.seat_type=="federal"]
print(fc.groupby(fc.year//10*10).uncontested.sum().to_string())
