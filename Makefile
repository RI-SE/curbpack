ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

.DEFAULT_GOAL := help
.PHONY: help start test ci-tests package test-curbcheck
export ONLY

help:
	@echo "make start            Start the local application"
	@echo "make test             Run the Studio functional tests"
	@echo "make test-curbcheck   Clone, apply R1, and run curbcheck"
	@echo "make ci-tests         Run mandatory CI checks. ONLY=name runs one check"
	@echo "make package          Build and smoke-test a binary for this operating system"

start:
	$(PYTHON) -m app

test:
	@$(PYTHON) scripts/ci/checks/tests.py

test-curbcheck:
	@sh tests/check/run.sh

ci-tests:
	@$(PYTHON) scripts/ci/run.py

package:
	$(PYTHON) scripts/build/package.py
