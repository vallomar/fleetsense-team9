-- Views over validated partitions produced by run.py.
CREATE OR REPLACE VIEW fact_trips AS SELECT * FROM read_parquet('data/clean/*.parquet');
CREATE OR REPLACE VIEW dim_zones AS SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv');
CREATE OR REPLACE TABLE dim_calendar AS SELECT DISTINCT CAST(pickup_datetime AS DATE) AS date, year(pickup_datetime) AS year, month(pickup_datetime) AS month, isodow(pickup_datetime) AS iso_weekday FROM fact_trips;
