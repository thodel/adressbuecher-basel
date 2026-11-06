PY ?= .venv/bin/python
SRC_DIR ?= $(HOME)/Documents/Adressbuecher_Basel

.PHONY: venv pages
venv:
	uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt

pages:  ## Seitenbilder byteidentisch übernehmen und 00_volumes.csv / 01_pages.csv anlegen
	$(PY) scripts/01_render_pages.py --src-dir "$(SRC_DIR)" --out data/pages --csv data/csv

RUN ?= basel-probe-gemini-v1
.PHONY: atr-fetch atr-lines
atr-fetch:  ## Ergebnisse eines ATR-Laufs von tei holen (RUN=...)
	$(PY) scripts/02_atr_batch.py fetch --run $(RUN)

atr-lines:  ## 02_lines.csv aus den geholten Läufen bauen (RUN=...)
	$(PY) scripts/02_atr_batch.py lines --run $(RUN)

PROBERUNS = basel-probe-gemini-v1 basel-probe-gpustack-v1
.PHONY: probe-fetch probe-compare
probe-fetch:  ## alle Probe-Läufe holen
	for r in $(PROBERUNS); do $(PY) scripts/02_atr_batch.py fetch --run $$r; done

probe-compare:  ## Abweichung je Leserpaar und CER gegen data/gt
	$(PY) scripts/03_compare_readers.py $(foreach r,$(PROBERUNS),--run $(r)) --gt data/gt

FULLRUNS = basel-gemini-v1 basel-qwen3vl30b-v1
.PHONY: fullrun-fetch fullrun-lines fullrun-parse probe-parse
fullrun-fetch:  ## alle Volllauf-Ergebnisse von tei holen
	for r in $(FULLRUNS); do $(PY) scripts/02_atr_batch.py fetch --run $$r; done

fullrun-lines:  ## 02_lines.csv aus allen Volllauf-Lesungen
	$(PY) scripts/02_atr_batch.py lines $(foreach r,$(FULLRUNS),--run $(r))

fullrun-parse:  ## Welle 2: Einträge und Gebäude aus dem Hauptleser → 04_entries.csv, 05_buildings.csv, 05_residents.csv
	$(PY) scripts/04_parse.py --run basel-gemini-v1 --reader gemini-3.8-flash --section einwohner --out data/csv/04_entries.csv
	$(PY) scripts/04_parse.py --run basel-gemini-v1 --reader gemini-3.8-flash --section berufe --out data/csv/04_berufe.csv
	$(PY) scripts/05_buildings.py --run basel-gemini-v1 --reader gemini-3.8-flash --out-buildings data/csv/05_buildings.csv --out-residents data/csv/05_residents.csv

probe-parse:  ## Welle 2 auf den Probeseiten
	$(PY) scripts/04_parse.py --run basel-probe-gemini-v1 --reader gemini-3.8-flash --section einwohner --out data/csv/04_entries_probe.csv
	$(PY) scripts/05_buildings.py --run basel-probe-gemini-v1 --reader gemini-3.8-flash --out-buildings data/csv/05_buildings_probe.csv --out-residents data/csv/05_residents_probe.csv
