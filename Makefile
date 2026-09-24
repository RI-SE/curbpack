INSTALL_DIR ?= $(HOME)/.local/bin
SUITE ?= all

.PHONY: list help build start-verification-run install uninstall clean test unittest baseline baseline-check checkout-baseline
.DEFAULT_GOAL := list

list help:
	@echo "list"
	@echo "build                    tmp/curbpack"
	@echo "start-verification-run   tmp/verification-run.sh  [CONFIRM_TMP_WIPE=1]"
	@echo "test                     testing/automation/suit-runner.sh"
	@echo "unittest                 go test ./..."
	@echo "baseline                 Create a three-repo baseline (NAME=… OVERRIDE_TESTS=1)"
	@echo "baseline-check           Verify a named baseline (NAME=…)"
	@echo "checkout-baseline        Detach all three repos at a named baseline (NAME=…)"
	@echo "install                  $(INSTALL_DIR)/curbpack"
	@echo "uninstall                $(INSTALL_DIR)/curbpack"
	@echo "clean                    tmp/curbpack"

build:
	mkdir -p tmp
	go build -o tmp/curbpack ./cmd/curbpack

start-verification-run:
	@scripts/start-verification-run.sh

baseline:
	@./scripts/baseline.sh

baseline-check:
	@./scripts/baseline.sh check

checkout-baseline:
	@./scripts/baseline.sh checkout

test:
	sh testing/automation/suit-runner.sh "$(SUITE)"

unittest:
	go test ./...

install: build
	mkdir -p "$(INSTALL_DIR)"
	cp tmp/curbpack "$(INSTALL_DIR)/curbpack"
	ln -sf curbpack "$(INSTALL_DIR)/curb"
    # todo also install skills etc from curbpack init (move it from there)
uninstall:
	rm -f "$(INSTALL_DIR)/curbpack" "$(INSTALL_DIR)/curb"

# Not rm -rf tmp: the reference-product clone is there.
clean:
	rm -f tmp/curbpack
