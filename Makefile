ingest:
	python download_data.py
	python run.py
validate:
	python -m pytest -q
analysis:
	python analyse.py
