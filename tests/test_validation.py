"""Range and temporal logic checks exercised through the production pipeline."""
from pathlib import Path
import duckdb
from run import build

def test_range_and_logic_quarantine(tmp_path):
 raw=tmp_path/'data/raw';raw.mkdir(parents=True)
 (raw/'taxi_zone_lookup.csv').write_text('LocationID,Borough,Zone,service_zone\n1,Test,Test,Test\n')
 c=duckdb.connect()
 c.execute('''create table sample as select timestamp '2025-01-01 12:00:00' as tpep_pickup_datetime, timestamp '2025-01-01 12:10:00' as tpep_dropoff_datetime, 1 as PULocationID,1 as DOLocationID,1.0 as trip_distance,10.0 as fare_amount,12.0 as total_amount,0.0 as tolls_amount,0.0 as mta_tax,0.0 as tip_amount,0.0 as extra,1.0 as improvement_surcharge,0.0 as congestion_surcharge,0.0 as airport_fee,1.0 as cbd_congestion_fee''')
 c.execute('insert into sample select * from sample')
 c.execute("update sample set fare_amount=-1 where rowid=1")
 c.execute('insert into sample select * from sample where rowid=0')
 c.execute("update sample set tpep_dropoff_datetime=timestamp '2025-01-01 11:59:00' where rowid=2")
 c.execute(f"copy sample to '{raw/'yellow_tripdata_2025-01.parquet'}' (format parquet)")
 build(tmp_path)
 d=duckdb.connect(str(tmp_path/'data/warehouse.duckdb'))
 assert d.execute('select rows_in,rows_loaded,rows_quarantined from ingestion_manifest').fetchone()==(3,1,2)
 q=d.execute(f"select reason_code from read_parquet('{tmp_path/'data/quarantine/2025-01.parquet'}') order by reason_code").fetchall()
 assert q==[('INVALID_DURATION',),('NEGATIVE_AMOUNT_REVIEW',)]
 before=d.execute('select count(*) from fact_trips').fetchone()[0];d.close()
 build(tmp_path)
 d=duckdb.connect(str(tmp_path/'data/warehouse.duckdb'))
 assert d.execute('select count(*) from fact_trips').fetchone()[0]==before
