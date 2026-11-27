ifeq ($(OS),Windows_NT)
PYTHON ?= $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,python)
else
# Use .venv only when it actually runs on this host (ignore a mounted foreign venv).
VENV_PYTHON := $(shell if .venv/bin/python -c 'import sys' >/dev/null 2>&1; then echo .venv/bin/python; fi)
PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python3)
endif

.DEFAULT_GOAL := help
PORT ?= 8770
.PHONY: help start stop test cicd test-installers package-installers package package-studio package-curbcheck start-verification-run test-curbcheck quality-diff

help:
	@echo "make start                   Start the local application"
	@echo "make stop                    Stop the process listening on port $(PORT)"
	@echo "make test                    Run the Studio functional tests"
	@echo "make start-verification-run  Clone the pin and fill tmp/verification-run.sh"
	@echo "                             DEVELOPER_MODE=TRUE allows a dirty Studio tree"
	@echo "make test-curbcheck          Source that run, apply R1, run curbcheck"
	@echo "                             Reuses DEVELOPER_MODE from env or the filled run"
	@echo "make cicd                    Run all PR checks, native builds and smoke tests"
	@echo "make test-installers         Run the Unix installer tests"
	@echo "make package-installers      Package installers and checksums"
	@echo "make package                 Build and smoke-test both native packages"
	@echo "make package-studio          Build and smoke-test Studio only"
	@echo "make package-curbcheck       Build and smoke-test curbcheck only"
	@echo "make quality-check           Run static analysis in .venv-quality"
	@echo "make quality-diff            Compare Python health in the worktree with HEAD"

start:
	$(PYTHON) -m app

stop:
	$(PYTHON) scripts/stop_app.py --port $(PORT)

test:
	@$(PYTHON) scripts/ci/checks/tests.py

start-verification-run:
	@sh scripts/start-verification-run.sh $(ARGS)

test-curbcheck:
	@sh tests/check/run.sh

# Keep PR jobs on these same targets; run sequentially and stop on failure.
# Native binaries are built for this host; other OS runners remain necessary.
cicd:
	+$(MAKE) test
	+$(MAKE) test-installers
	+$(MAKE) package-installers
	+$(MAKE) package-studio
	+$(MAKE) package-curbcheck

test-installers:
	$(PYTHON) -m unittest tests.test_installers

package-installers:
	$(PYTHON) scripts/build/package_installers.py

package: package-studio package-curbcheck

package-studio:
	$(PYTHON) scripts/build/package_studio.py

package-curbcheck:
	$(PYTHON) scripts/build/package_curbcheck.py

### QUALITY CHECKS ###
# pylint 4 does not publish builds for Python 3.9. Do not reuse $(PYTHON):
# the project .venv may be Apple's Command Line Tools interpreter.
# make does not expand shell aliases, so look up the conda binary itself.
QUALITY_VENV := .venv-quality
QUALITY_PYTHON := $(QUALITY_VENV)/bin/python
QUALITY_PY := 3.12
QUALITY_CONDA := $(shell command -v micromamba 2>/dev/null || command -v conda 2>/dev/null || command -v mamba 2>/dev/null)

.PHONY: quality-tools quality-check quality-diff

$(QUALITY_VENV)/.installed: requirements-quality.txt
	@if ! $(QUALITY_PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then \
	  rm -rf $(QUALITY_VENV); \
	  if [ -z "$(QUALITY_CONDA)" ]; then \
	    echo "quality-check needs micromamba, conda, or mamba to create a Python $(QUALITY_PY) environment." >&2; \
	    exit 1; \
	  fi; \
	  "$(QUALITY_CONDA)" create -y -p "$(CURDIR)/$(QUALITY_VENV)" python=$(QUALITY_PY) pip; \
	fi
	$(QUALITY_PYTHON) -m pip install -r requirements-quality.txt
	touch $@

quality-tools: $(QUALITY_VENV)/.installed

quality-check: quality-tools
	$(QUALITY_PYTHON) scripts/ci/checks/quality.py

quality-diff:
	$(PYTHON) scripts/ci/checks/diff_quality.py