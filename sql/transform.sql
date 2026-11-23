-- transform.sql: projection from validated rows (reason_code empty) into the clean
-- fact schema for one source month. run.py rewrites this file per loaded file; the last
-- written month is shown. Output columns feed fact_trips; definitions: docs/design.md.
SELECT 'yellow_tripdata_2025-12.parquet' AS source_file, source_row, tpep_pickup_datetime AS pickup_datetime,
          tpep_dropoff_datetime AS dropoff_datetime, PULocationID AS zone_id, DOLocationID AS dropoff_zone_id,
          CAST(fare_amount AS DECIMAL(18,2)) AS fare_amount, trip_distance,
          date_diff('second',tpep_pickup_datetime,tpep_dropoff_datetime)/60.0 AS duration_minutes,
          'unknown' AS booking_channel,
          CAST(total_amount AS DECIMAL(18,2)) AS revenue_with_charges,
          CAST(tolls_amount AS DECIMAL(18,2)) + CAST(extra AS DECIMAL(18,2)) + CAST(improvement_surcharge AS DECIMAL(18,2)) + CAST(congestion_surcharge AS DECIMAL(18,2)) + CAST(airport_fee AS DECIMAL(18,2)) + CAST(cbd_congestion_fee AS DECIMAL(18,2)) AS charges,
          CAST(total_amount AS DECIMAL(18,2))-(CAST(tolls_amount AS DECIMAL(18,2)) + CAST(extra AS DECIMAL(18,2)) + CAST(improvement_surcharge AS DECIMAL(18,2)) + CAST(congestion_surcharge AS DECIMAL(18,2)) + CAST(airport_fee AS DECIMAL(18,2)) + CAST(cbd_congestion_fee AS DECIMAL(18,2))) AS revenue_without_charges
          FROM checked WHERE reason_code='';
