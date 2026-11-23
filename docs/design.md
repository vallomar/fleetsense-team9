# Design document

Owner: Omar Ahmed Mohamed, Team No 9. Created 23 November 2026, late catch-up, not backdated. Mentor approval has not been obtained.

## Sources

NYC TLC yellow-taxi trip records, January through December 2025, plus taxi-zone lookup. URLs in sources.json; SHA-256 and sizes in download_manifest.json. Official landing page: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page . Dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf . TLC cautions that vendor records may be incomplete or inaccurate.

These are New York taxi observations, not real patient transport records. They do not identify booking channel, hospital appointments, fleet size, driver or vehicle. Harbourline is a simulated client in the assignment. Its hospital/street classification cannot be recovered from this source alone.

## Warehouse model

Grain of fact_trips: one accepted source row, keyed by source_file and source_row. Raw files immutable; ingestion_manifest stores SHA-256 and row accounting per file. dim_zones uses the official LocationID. dim_calendar has one accepted pickup date, year, month and ISO weekday. hourly_demand groups pickup zone and local pickup hour. Monetary outputs use DECIMAL(18,2), USD. Taxi timestamps are treated as supplied NYC local wall times, not UTC; no physical elapsed-time claim across DST folds.

The booking_channel enum is hospital_booked, street_hail or unknown. Only authoritative source values can set the first two. All TLC observations are unknown. Every aggregate includes all three counts, whose sum must equal trips. assert_channel_complete raises an error if asked for a two-category hospital/street report before the missing data is supplied. Tests use deliberately synthetic channel rows, not fabricated client evidence.

## Metrics, defined once in metrics/__init__.py

- Trips: count of accepted source records, grouped by pickup date/zone.
- Revenue with charges: sum of total_amount, passenger charges including recorded tips and tax, excluding unrecorded cash tips. Not net operator revenue.
- CR-1 charges: tolls_amount + extra + improvement_surcharge + congestion_surcharge + airport_fee + cbd_congestion_fee. mta_tax is retained because it is a tax. Airport and CBD fees are conservatively treated as surcharges; confirm this convention with the reviewer.
- Revenue without charges: total_amount minus those six components. The difference must match charges exactly, using decimal arithmetic. This is not equal to metered fare because tips and tax remain.
- Average fare: mean fare_amount, not average total passenger charge.
- Duration: mean of dropoff minus pickup in minutes, for accepted records with duration greater than zero and no more than 24 hours.
- Utilisation proxy: sum of occupied trip duration in hours. This is work volume, not a vehicle utilisation percentage. Overlapping trips and missing vehicle IDs make fleet capacity utilisation unknowable.
- Hourly and monthly seasonality charts use average accepted trips per calendar day, not raw totals alone. Weekdays use the number of occurrences of each weekday in the year to avoid a 52/53-day denominator bias.

## Validation and risk

Quarantine null/nonfinite money, invalid zones, negative core charges, nonpositive/over-24-hour duration, invalid distance or pickup outside source month. Each row carries all applicable reason codes. rows_in = rows_loaded + rows_quarantined is checked per month. No money field is silently imputed to zero. The strict policy removes 26.6% of source rows, mainly due to null money fields, so accepted-record charts are selection-biased and cannot stand for total city demand. The quarantine is evidence to review, not data to hide.

Missing passenger_count or RatecodeID is not a rejection when the required metrics do not use it. Zone IDs 264 and 265 remain in metrics as unknown/outside locations, but geographic top/bottom charts use named zones 1–263 and include zero-count zones. Refunds/negative charges are quarantined for a separate accounting policy, not called fraudulent. High positive fares are retained rather than clipped without authority.

## Reproducibility and ownership

Run download, pipeline, charts and tests as documented in README. The second pipeline run skips the same checksummed files and preserves row counts. No raw or clean trip data is committed. Omar owns ingestion, quality, warehouse, metrics, analysis, CR-1 and reproducibility because the team currently has one member. No claim is made that a teammate reviewed this work. Use a task branch and a pull request, with human review before merge. Do not backdate commits or approval.
