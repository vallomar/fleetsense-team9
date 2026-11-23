"""Canonical metric SQL. Money is decimal USD, not binary floating point."""
SURCHARGES = ('extra','improvement_surcharge','congestion_surcharge','airport_fee','cbd_congestion_fee')
# mta_tax is a tax, not a surcharge. Tips and tax remain in both CR-1 measures.
CHARGES_SQL = ' + '.join(f'CAST({c} AS DECIMAL(18,2))' for c in ('tolls_amount',)+SURCHARGES)
METRICS_SQL = '''
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
'''
def assert_channel_complete(con):
    n=con.execute("select count(*) from fact_trips where booking_channel='unknown'").fetchone()[0]
    if n:
        raise ValueError(f'{n} trips lack authoritative booking channel; two-way hospital/street reporting is blocked')
