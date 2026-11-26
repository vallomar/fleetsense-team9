# Verification record, 26 November 2026

Owner: Omar Ahmed Mohamed, Team No 9. Re-checked the Week 1-3 deliverables today. No new analysis claims, no code, metric or evidence changes.

## What was re-run and compared

1. Test suite re-run locally (`python3 -m pytest -q`, duckdb 1.5.6, pytest 9.2.0): **4 passed, 1 skipped**. The skipped test is the full-data integration test; it needs `data/warehouse.duckdb`, which is not committed by policy.
2. Single-source definitions confirmed: the charge expression in `sql/transform.sql` matches `metrics/__init__.py` `CHARGES_SQL` exactly (tolls_amount, extra, improvement_surcharge, congestion_surcharge, airport_fee, cbd_congestion_fee). `run.py` builds all revenue columns from that module.
3. `reports/totals.json` matches the README and `docs/cr1.md` figures: revenue with charges $1,061,002,515.85, without charges $841,275,900.12, difference $219,726,615.73, over 35,759,618 accepted of 48,722,602 source rows (26.6% quarantined).
4. `docs/design.md` metric definitions match the module: booking-channel reconciliation, average metered fare (not average total charge), duration bounds (0 < d <= 24h), and the utilisation proxy wording (occupied trip hours, not a vehicle utilisation percentage).

No data files were added. Raw, clean and quarantine data remain local-only.
