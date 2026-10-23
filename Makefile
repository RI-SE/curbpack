ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

.DEFAULT_GOAL := help
.PHONY: help start test ci-tests package
export ONLY

help:
	@echo "make start      Start the local application"
	@echo "make test       Run the functional tests"
	@echo "make ci-tests   Run mandatory CI checks. ONLY=name runs one check"
	@echo "make package    Build and smoke-test a binary for this operating system"

start:
	$(PYTHON) -m app

test:
	$(PYTHON) scripts/ci/checks/tests.py

ci-tests:
	$(PYTHON) scripts/ci/run.py

package:
	$(PYTHON) scripts/build/package.py
