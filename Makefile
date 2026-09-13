SCIENTIFIC_PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
VERSION ?= $(shell python3 -c 'import json; print(json.load(open("project_status.json"))["latest_version"])')
DOCUMENT ?= $(shell python3 -c 'import json; print(json.load(open("project_status.json"))["document"])')

.PHONY: check check-inference-components check-robustness check-scalar check-application readme pdf article release

check-inference-components:
	$(SCIENTIFIC_PYTHON) scripts/validar_componentes_inferencia.py --check

check-robustness:
	$(SCIENTIFIC_PYTHON) -m unittest discover -s tests -p 'test_c09*.py' -v

check-scalar:
	$(SCIENTIFIC_PYTHON) -m unittest discover -s tests -p 'test_c10*.py' -v

check-application:
	$(SCIENTIFIC_PYTHON) -m unittest discover -s tests -p 'test_c11*.py' -v

check: check-robustness check-scalar check-application
	$(SCIENTIFIC_PYTHON) scripts/reproduzir_tg.py --check
	$(SCIENTIFIC_PYTHON) scripts/validar_orf.py --check
	$(SCIENTIFIC_PYTHON) scripts/benchmark_orf.py --verify-only results/C05/checked_benchmark_results.json
	$(SCIENTIFIC_PYTHON) scripts/validar_simulador.py --check
	$(SCIENTIFIC_PYTHON) scripts/validar_componentes_inferencia.py --check
	python3 scripts/checagens_preliminares.py
	python3 scripts/update_readme.py --check
	python3 scripts/verify_release.py $(VERSION)

readme:
	python3 scripts/update_readme.py
	python3 scripts/update_document_state.py

pdf:
	python3 scripts/build_release.py --version $(VERSION) --document $(DOCUMENT) --build-only

release: check-robustness check-scalar check-application
	$(SCIENTIFIC_PYTHON) scripts/reproduzir_tg.py --check
	$(SCIENTIFIC_PYTHON) scripts/validar_orf.py --check
	$(SCIENTIFIC_PYTHON) scripts/benchmark_orf.py --verify-only results/C05/checked_benchmark_results.json
	$(SCIENTIFIC_PYTHON) scripts/validar_simulador.py --check
	$(SCIENTIFIC_PYTHON) scripts/validar_componentes_inferencia.py --check
	python3 scripts/checagens_preliminares.py
	python3 scripts/update_readme.py
	python3 scripts/update_document_state.py
	python3 scripts/build_release.py --version $(VERSION) --document $(DOCUMENT)
	python3 scripts/verify_release.py $(VERSION)

article:
	python3 scripts/build_article.py
