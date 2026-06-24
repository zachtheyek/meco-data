import duckdb
con=duckdb.connect(); B="raw/consol_ballots.csv"
def q(s): return con.execute(s).fetchdf()
# Does the same seat NUMBER map to different names over time? (federal)
print("=== P.001 across federal elections ===")
print(q(f"""select election,date,state,seat from '{B}'
 where seat like 'P.001 %' and election like 'GE-%'
 group by all order by date""").to_string(index=False))
print("\n=== seat NAME stability: a current seat e.g. 'Bagan' across time ===")
print(q(f"""select election,date,seat,state from '{B}' where seat like '%Bagan%' and election like 'GE-%' group by all order by date""").to_string(index=False))
print("\n=== how many distinct (number+name) federal seat strings per GE? trend ===")
print(q(f"""select election, count(distinct seat) seats from '{B}' where seat like 'P.%' and election like 'GE-%' group by 1 order by 1""").head(40).to_string(index=False))
print("\n=== are seat strings ever reused with same number+name across non-adjacent eras? count of GEs each federal seat-string appears in ===")
print(q(f"""with t as (select seat, count(distinct election) ne from '{B}' where election like 'GE-%' and seat like 'P.%' group by 1)
 select ne as num_GEs_seat_appears_in, count(*) n_seatstrings from t group by 1 order by 1""").to_string(index=False))
