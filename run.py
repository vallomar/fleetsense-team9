"""Incremental, audited TLC warehouse and Week 3 outputs. Run: python run.py."""
import argparse, json, hashlib, pathlib, datetime
import duckdb
from metrics import CHARGES_SQL, METRICS_SQL
ROOT=pathlib.Path(__file__).parent

def build(root=ROOT):
    root=pathlib.Path(root); raw=root/'data/raw'; clean=root/'data/clean'; quarantine=root/'data/quarantine'
    out=root/'reports'; sql=root/'sql'
    for p in (clean,quarantine,out,sql): p.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(str(root/'data/warehouse.duckdb'))
    con.execute("SET memory_limit='1GB'"); con.execute('SET threads=2')
    con.execute('CREATE TABLE IF NOT EXISTS ingestion_manifest (file VARCHAR PRIMARY KEY, sha256 VARCHAR, rows_in BIGINT, rows_loaded BIGINT, rows_quarantined BIGINT)')
    for p in sorted(raw.glob('yellow_tripdata_*.parquet')):
        digest=hashlib.sha256(p.read_bytes()).hexdigest(); old=con.execute('SELECT sha256 FROM ingestion_manifest WHERE file=?',[p.name]).fetchone()
        if old:
            if old[0]!=digest: raise ValueError(f'{p.name} changed; review source revision before replacing')
            print('Already loaded:',p.name,flush=True); continue
        month=p.stem[-7:]; year,mm=map(int,month.split('-')); start=datetime.date(year,mm,1); end=datetime.date(year+int(mm==12),mm%12+1,1)
        con.read_parquet(str(p)).create_view('source_month', replace=True)
        con.execute('CREATE OR REPLACE TEMP VIEW raw_month AS SELECT row_number() OVER () AS source_row, * FROM source_month')
        cols={r[0].lower() for r in con.execute('describe raw_month').fetchall()}
        required={'tpep_pickup_datetime','tpep_dropoff_datetime','pulocationid','dolocationid','fare_amount','total_amount','trip_distance','tolls_amount','mta_tax','tip_amount','extra','improvement_surcharge','congestion_surcharge','airport_fee','cbd_congestion_fee'}
        if not required<=cols: raise ValueError(f'Missing fields: {required-cols}')
        channels="CASE WHEN booking_channel IN ('hospital_booked','street_hail') THEN booking_channel ELSE 'unknown' END" if 'booking_channel' in cols else "'unknown'"
        reason=f"""concat_ws('|',
          CASE WHEN tpep_pickup_datetime IS NULL OR tpep_dropoff_datetime IS NULL THEN 'NULL_DATETIME' END,
          CASE WHEN tpep_pickup_datetime < DATE '{start}' OR tpep_pickup_datetime >= DATE '{end}' THEN 'OUTSIDE_SOURCE_MONTH' END,
          CASE WHEN tpep_dropoff_datetime <= tpep_pickup_datetime OR date_diff('second',tpep_pickup_datetime,tpep_dropoff_datetime)>86400 THEN 'INVALID_DURATION' END,
          CASE WHEN trip_distance IS NULL OR NOT isfinite(trip_distance) OR trip_distance<0 THEN 'INVALID_DISTANCE' END,
          CASE WHEN PULocationID IS NULL OR PULocationID NOT BETWEEN 1 AND 265 OR DOLocationID IS NULL OR DOLocationID NOT BETWEEN 1 AND 265 THEN 'INVALID_ZONE' END,
          CASE WHEN {' OR '.join(f'{c} IS NULL OR NOT isfinite({c})' for c in ['total_amount','fare_amount','tolls_amount','mta_tax','tip_amount','extra','improvement_surcharge','congestion_surcharge','airport_fee','cbd_congestion_fee'])} THEN 'MISSING_OR_NONFINITE_MONEY' END,
          CASE WHEN total_amount<0 OR fare_amount<0 OR tolls_amount<0 OR extra<0 OR improvement_surcharge<0 OR congestion_surcharge<0 OR airport_fee<0 OR cbd_congestion_fee<0 THEN 'NEGATIVE_AMOUNT_REVIEW' END)"""
        con.execute(f'CREATE OR REPLACE TEMP VIEW checked AS SELECT *, {reason} AS reason_code FROM raw_month')
        dest=clean/(month+'.parquet'); qdest=quarantine/(month+'.parquet')
        transform=f"""SELECT '{p.name}' AS source_file, source_row, tpep_pickup_datetime AS pickup_datetime,
          tpep_dropoff_datetime AS dropoff_datetime, PULocationID AS zone_id, DOLocationID AS dropoff_zone_id,
          CAST(fare_amount AS DECIMAL(18,2)) AS fare_amount, trip_distance,
          date_diff('second',tpep_pickup_datetime,tpep_dropoff_datetime)/60.0 AS duration_minutes,
          {channels} AS booking_channel,
          CAST(total_amount AS DECIMAL(18,2)) AS revenue_with_charges,
          {CHARGES_SQL} AS charges,
          CAST(total_amount AS DECIMAL(18,2))-({CHARGES_SQL}) AS revenue_without_charges
          FROM checked WHERE reason_code=''"""
        transform_doc=('-- transform.sql: projection from validated rows (reason_code empty) into the clean\n'
          '-- fact schema for one source month. run.py rewrites this file per loaded file; the last\n'
          '-- written month is shown. Output columns feed fact_trips; definitions: docs/design.md.\n')
        (sql/'transform.sql').write_text(transform_doc+transform+';\n')
        con.execute(f"COPY ({transform}) TO '{dest}' (FORMAT PARQUET)")
        con.execute(f"COPY (SELECT * FROM checked WHERE reason_code<>'') TO '{qdest}' (FORMAT PARQUET)")
        n=con.execute('select count(*) from checked').fetchone()[0]; loaded=con.execute(f"select count(*) from read_parquet('{dest}')").fetchone()[0]; bad=con.execute(f"select count(*) from read_parquet('{qdest}')").fetchone()[0]
        assert n==loaded+bad
        con.execute('insert into ingestion_manifest values (?,?,?,?,?)',[p.name,digest,n,loaded,bad]); print(month,n,loaded,bad,flush=True)
    con.execute(f"CREATE OR REPLACE VIEW fact_trips AS SELECT * FROM read_parquet('{clean}/*.parquet')")
    con.execute(f"CREATE OR REPLACE VIEW dim_zones AS SELECT * FROM read_csv_auto('{raw/'taxi_zone_lookup.csv'}')")
    con.execute('CREATE OR REPLACE TABLE dim_calendar AS SELECT DISTINCT CAST(pickup_datetime AS DATE) AS date, year(pickup_datetime) AS year, month(pickup_datetime) AS month, isodow(pickup_datetime) AS iso_weekday FROM fact_trips')
    warehouse_doc='''-- warehouse.sql: the FleetSense DuckDB warehouse objects, created by run.py over the
-- validated parquet partitions. Run from the repository root after `python run.py`.
-- Grain, metric and channel definitions: docs/design.md.

-- fact_trips: one row per accepted TLC source row, keyed by source_file and source_row.
-- Rejected rows are never here; they sit in data/quarantine with reason codes.
CREATE OR REPLACE VIEW fact_trips AS SELECT * FROM read_parquet('data/clean/*.parquet');

-- dim_zones: official TLC taxi-zone lookup (LocationID, Borough, Zone, service_zone).
CREATE OR REPLACE VIEW dim_zones AS SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv');

-- dim_calendar: one row per accepted pickup date, with year, month and ISO weekday.
-- Used to normalise seasonality by calendar exposure (52/53-day safe).
CREATE OR REPLACE TABLE dim_calendar AS SELECT DISTINCT CAST(pickup_datetime AS DATE) AS date, year(pickup_datetime) AS year, month(pickup_datetime) AS month, isodow(pickup_datetime) AS iso_weekday FROM fact_trips;
'''
    aggregate_docs={
     'by_zone':'-- by_zone: trips, booking-channel counts and CR-1 revenue per pickup zone (accepted records).\n',
     'by_hour':'-- by_hour: trips, booking-channel counts and CR-1 revenue per pickup hour of day (accepted records).\n',
     'by_weekday':'-- by_weekday: trips, booking-channel counts and CR-1 revenue per ISO weekday (accepted records).\n',
     'by_month':'-- by_month: trips, booking-channel counts and CR-1 revenue per calendar month (accepted records).\n',
     'by_zone_day':'-- by_zone_day: trips, booking-channel counts and CR-1 revenue per pickup zone and date.\n-- Used for zone-day reconciliation of the hourly demand table.\n',
     'hourly_demand':'-- hourly_demand: accepted trips and CR-1 revenue measures per pickup zone and hour.\n-- A query on this table returns rows for each zone and hour in the accepted data;\n-- it feeds the seasonality charts and the zone-day reconciliation.\n',
    }
    groupings={'by_zone':'zone_id','by_hour':'hour(pickup_datetime) AS hour','by_weekday':'isodow(pickup_datetime) AS iso_weekday','by_month':"strftime(pickup_datetime,'%Y-%m') AS month",'by_zone_day':'zone_id, CAST(pickup_datetime AS DATE) AS date','hourly_demand':"zone_id, date_trunc('hour',pickup_datetime) AS hour"}
    for name,group in groupings.items():
        query=f'SELECT {group}, {METRICS_SQL} FROM fact_trips GROUP BY ALL'
        if name=='hourly_demand':
            (sql/(name+'.sql')).write_text(aggregate_docs[name]+'CREATE OR REPLACE TABLE hourly_demand AS '+query+';\n')
            warehouse_doc+='\n-- hourly_demand: accepted trips and CR-1 revenue per pickup zone and hour (table).\n-- Full statement with its purpose comment: sql/hourly_demand.sql.\nCREATE OR REPLACE TABLE hourly_demand AS '+query+';\n'
        else:
            (sql/(name+'.sql')).write_text(aggregate_docs[name]+query+';\n')
        con.execute('CREATE OR REPLACE TABLE '+name+' AS '+query)
        con.execute(f"COPY (SELECT * FROM {name} ORDER BY 1) TO '{out/(name+'.csv')}' (HEADER, DELIMITER ',')")
    (sql/'warehouse.sql').write_text(warehouse_doc)
    con.execute(f"COPY (SELECT * FROM ingestion_manifest ORDER BY file) TO '{out/'quality_counts.csv'}' (HEADER)")
    con.execute(f"COPY (SELECT reason_code,count(*) AS records FROM read_parquet('{quarantine}/*.parquet') GROUP BY 1 ORDER BY 2 DESC) TO '{out/'quarantine_reasons.csv'}' (HEADER)")
    totals=dict(zip([x[0] for x in con.execute(f'SELECT {METRICS_SQL} FROM fact_trips').description],con.execute(f'SELECT {METRICS_SQL} FROM fact_trips').fetchone()))
    (out/'totals.json').write_text(json.dumps(totals,default=str,indent=2)); print(totals,flush=True)
    con.close()
if __name__=='__main__': build()
