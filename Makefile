INSTALL_DIR ?= $(HOME)/.local/bin
SUITE ?= all

.PHONY: list help build start-verification-run install uninstall clean test
.DEFAULT_GOAL := list

list help:
	@echo "list"
	@echo "build                    tmp/curbpack"
	@echo "start-verification-run   tmp/verification-run.sh  [CONFIRM_TMP_WIPE=1]"
	@echo "test                     docs/testing/automation/suit-runner.sh"
	@echo "install                  $(INSTALL_DIR)/curbpack"
	@echo "uninstall                $(INSTALL_DIR)/curbpack"
	@echo "clean                    tmp/curbpack"

build:
	mkdir -p tmp
	go build -o tmp/curbpack ./cmd/curbpack

start-verification-run:
	@scripts/start-verification-run.sh

test:
	sh docs/testing/automation/suit-runner.sh "$(SUITE)"

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
	