ifeq ($(OS),Windows_NT)
PYTHON ?= $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,python)
else
# Use .venv only when it actually runs on this host (ignore a mounted foreign venv).
VENV_PYTHON := $(shell if .venv/bin/python -c 'import sys' >/dev/null 2>&1; then echo .venv/bin/python; fi)
PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python3)
endif

.DEFAULT_GOAL := help
PORT ?= 8770
.PHONY: help start stop test cicd test-installers package-installers package package-studio package-curbcheck start-verification-run test-curbcheck

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
