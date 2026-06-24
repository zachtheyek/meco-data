import duckdb
con = duckdb.connect()
B = "raw/consol_ballots.csv"
S = "raw/consol_stats.csv"
def q(sql): return con.execute(sql).fetchdf()

print("=== ballots columns ==="); print(list(q(f"select * from '{B}' limit 1").columns))
print("\n=== election codes (count contests = distinct date,state,seat) ===")
print(q(f"""select election, min(date) d0, max(date) d1, count(distinct state||'|'||seat) seats, count(*) n_rows
          from '{B}' group by election order by d0""").to_string(index=False))
print("\n=== seat prefixes (P. vs N.) ===")
print(q(f"""select substr(seat,1,2) pfx, count(distinct seat) n from '{B}' group by 1 order by 2 desc""").to_string(index=False))
print("\n=== result categories ===")
print(q(f"select result, count(*) n from '{B}' group by 1 order by 2 desc").to_string(index=False))
print("\n=== distinct states ===")
print(q(f"select state, count(distinct seat) seats from '{B}' group by 1 order by 1").to_string(index=False))
print("\n=== how is federal vs state distinguished? sample state-election rows ===")
print(q(f"""select distinct election, state from '{B}' where election not like 'GE-%' limit 20""").to_string(index=False))
