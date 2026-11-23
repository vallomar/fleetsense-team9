-- by_hour: trips, booking-channel counts and CR-1 revenue per pickup hour of day (accepted records).
SELECT hour(pickup_datetime) AS hour, 
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
