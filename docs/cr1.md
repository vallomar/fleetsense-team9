# CR-1 impact estimate

Issued by project brief 22 November 2026. Implemented in the catch-up work 23 November 2026.

## Change

Add passenger revenue with charges, revenue without tolls/surcharges, and their difference to each pickup-zone aggregate. Definitions live in metrics/__init__.py and flow into all SQL outputs, including hourly demand and zone-day reconciliation.

Included exclusions: tolls_amount, extra, improvement_surcharge, congestion_surcharge, airport_fee and cbd_congestion_fee. Tax and recorded tips remain. Cash tips are unavailable. The source's total_amount is not net operator revenue. This explicit convention is reviewable, not an assertion that the client approved it.

## Estimate, not measured labour

Planning estimate: 2–4 hours for an existing stable warehouse: 30–45 minutes to confirm fee definitions and nulls, 45–90 minutes for module/SQL changes, 30–60 minutes for tests and validation, 15–45 minutes for charts/documentation. A channel dataset or changed null policy can add work. This estimate is not a timesheet and does not claim Omar personally spent those hours.

## Risks and controls

- 2025 adds CBD fee: include it explicitly, fail on missing schema rather than lose it silently.
- Null fee fields: quarantine, publish counts; totals only describe accepted records.
- Double subtraction: exact decimal identity with charges is tested.
- Tax/airport interpretation: clearly document included columns and keep definitions in one place.
- Zone attribution: pickup zone, not a split across pickup/dropoff; say so in chart labels.
- Booking channel: keep unknown separate. Client-specific hospital/street acceptance remains blocked.

## Reproduction

Run python run.py. reports/by_zone.csv contains the three CR-1 money columns, and sql/by_zone.sql reproduces them. Sum of with minus without minus charges is exactly zero across zones. Accepted-record totals: with $1,061,002,515.85; without $841,275,900.12; difference $219,726,615.73.
