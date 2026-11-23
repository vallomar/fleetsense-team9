-- warehouse.sql: the FleetSense DuckDB warehouse objects, created by run.py over the
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

-- hourly_demand: accepted trips and CR-1 revenue per pickup zone and hour (table).
-- Full statement with its purpose comment: sql/hourly_demand.sql.
CREATE OR REPLACE TABLE hourly_demand AS SELECT zone_id, date_trunc('hour',pickup_datetime) AS hour, 
count(*) AS trips,
count(*) FILTER (WHERE booking_channel='hospital_booked') AS hospital_booked_trips,
count(*) FILTER (WHERE booking_channel='street_hail') AS street_hail_trips,
count(*) FILTER (WHERE booking_channel='unknown') AS unknown_channel_trips,
sum(revenue_with_charges) AS revenue_with_charges,
sum(revenue_without_charges) AS revenue_without_charges,
sum(charges) AS charges,
avg(fare_amount) AS average_metered_fare,
avg(duration_minutes) AS average_duration_minutes,
sum(duration_minutes)/60.0 AS occupied_trip_hours_proxy
 FROM fact_trips GROUP BY ALL;
