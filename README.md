# FleetSense, Team No 9: Week 3

Owner: Omar Ahmed Mohamed. Prepared 23 November 2026.

## Status

This is real code and analysis over all twelve 2025 NYC TLC yellow-taxi files. It is **not a complete internship submission**. The hospital-booking requirement is blocked because yellow-taxi data has no booking-channel field. All real records remain `unknown`, never guessed from location, payment type, rate code or vendor. No mentor message or peer review has been sent. Deployment, personal videos and final report are still pending.

## Run

Python 3.11+ recommended. Install `requirements.txt`, then:

```sh
python download_data.py
python run.py
python analyse.py
python -m pytest -q
python run.py  # second run must add no rows
```

The download URLs in `sources.json` were extracted from the official TLC page. Downloads total about 830 MB. Clean/quarantine files and the local database add storage. Data never belongs in Git. New month: add the official file URL to `sources.json`, download it to `data/raw`, then run the same pipeline. Changed source files fail closed until explicitly reviewed.

`run.py` uses file name + SHA-256 to skip loaded files. Each accepted record retains source file and source-row identity. Identical-looking rows within a file are retained because TLC supplies no unique trip ID and they may be distinct trips. Idempotence means rerunning the same source files adds no rows, not speculative deduplication of legitimate trips.

## Results and limitations

48,722,602 source rows = 35,759,618 accepted + 12,962,984 quarantined (26.6%). The large quarantine share is material. Most quarantine rows have missing money fields; they must not silently become zero. All charts and revenue describe **accepted records only**, not total NYC demand or operator income. See `reports/quality_counts.csv` and `reports/quarantine_reasons.csv`. A revised null policy requires mentor/data-owner agreement and rerunning the evidence.

Accepted passenger charges are $1,061,002,515.85, versus $841,275,900.12 after the defined toll/surcharge exclusions, a $219,726,615.73 difference. These include card tips and tax; cash tips are absent. This is passenger-charge revenue, not net operator earnings. See `docs/design.md` for exact definitions.

Six charts and their CSV data are in `reports/`. The actual-data hospital/street two-way reconciliation intentionally fails closed. Synthetic channel tests pass, but do not count as business evidence.

## Structure

- `metrics/`: one canonical metric definition module
- `run.py`: validation, incremental load, quarantine and aggregate tables
- `sql/`: generated reproducible SQL for each output
- `analyse.py`: six evidence charts
- `tests/`: exact-money, channel and full-data reconciliation tests
- `docs/`: metric definitions, decision log, CR-1 estimate, proposed mentor update
- `reports/`: quality evidence, aggregates and charts, no trip-level data

No real patient records or hospital booking identifiers are present. NYC data describes New York taxis, not Harbourline's Newark fleet. No claim about 120 vehicles or clinical demand is inferred from it.
