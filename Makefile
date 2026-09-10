VERSION ?= $(shell python3 -c 'import json; print(json.load(open("project_status.json"))["latest_version"])')
DOCUMENT ?= $(shell python3 -c 'import json; print(json.load(open("project_status.json"))["document"])')

.PHONY: check readme pdf release
check:
	python3 scripts/checagens_preliminares.py
	python3 scripts/update_readme.py --check
	python3 scripts/verify_release.py $(VERSION)

readme:
	python3 scripts/update_readme.py
	python3 scripts/update_document_state.py

pdf:
	python3 scripts/build_release.py --version $(VERSION) --document $(DOCUMENT) --build-only

release:
	python3 scripts/checagens_preliminares.py
	python3 scripts/update_readme.py
	python3 scripts/update_document_state.py
	python3 scripts/build_release.py --version $(VERSION) --document $(DOCUMENT)
	python3 scripts/verify_release.py $(VERSION)
