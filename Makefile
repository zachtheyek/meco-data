# Use the local venv if present (it has pandas/pyarrow), else system python3.
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: refresh data
refresh:  ## fetch the latest MECo corpus and rebuild out/ (one-liner refresh)
	$(PY) fetch_raw.py && $(PY) pipeline.py
	@echo "Refreshed. Commit & push, then the downstream sites self-update on their weekly build."

data:     ## rebuild out/ from the current raw/ snapshot (no fetch)
	$(PY) pipeline.py
