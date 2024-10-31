###################################################
# Calculated Variables
###################################################
TOP ?= $(shell git rev-parse --show-toplevel)
NUM_SUBMODULES ?=  $(shell ls $(IMPORT_DIR)/ | wc -l | xargs)

###################################################
# Required Executables
###################################################
REALPATH ?= $(if $(shell which grealpath),grealpath,realpath)
ECHO ?= $(if $(shell which gecho),gecho,echo)
TR ?= $(if $(shell which gtr),gtr,tr)
GIT ?= git
PYTHON ?= python
RMRF ?= rm -rf

###################################################
# Extra Makefile Targets
###################################################
# Saves initial values so that we can filter them later
VARS_OLD := $(.VARIABLES)
SHELL := /bin/bash

define bsg_fn_upper
	$(eval $@_word = $(1))
	$(ECHO) ${$@_word} | $(TR) a-z A-Z
endef
define bsg_fn_lower
	$(eval $@_word = $(1))
	$(ECHO) ${$@_word} | $(TR) A-Z a-z
endef
bsg_var_blank :=
define bsg_var_newline
$(bsg_var_blank)
endef
define bsg_rel_path
	$(shell $(REALPATH) --relative-to=$(1) $(2))
endef

###################################################
# Paths
###################################################
CORES_DIR ?= $(TOP)/basejump_stl_cores
VENV_DIR ?= $(TOP)/.venv
IMPORT_DIR ?= $(TOP)/import
BASEJUMP_STL_DIR ?= $(IMPORT_DIR)/basejump_stl
SURELOG_DIR ?= $(IMPORT_DIR)/Surelog
VERILATOR_DIR ?= $(IMPORT_DIR)/verilator

SUBMODULE_GITS ?= $(addsuffix /.git, $(BASEJUMP_STL_DIR) $(SURELOG_DIR) $(VERILATOR_DIR))

###################################################
# Commands
###################################################
VENV_SCRIPT ?= $(VENV_DIR)/bin/activate
VENV_ACTIVATE ?= source $(VENV_SCRIPT)
PYTHON_RUN ?= $(VENV_ACTIVATE) && python

SURELOG_BIN ?= $(VENV_DIR)/bin/surelog
VERILATOR_BIN ?= $(VENV_DIR)/bin/verilator

###################################################
# Targets
###################################################
.DEFAULT_GOAL: help
.PHONY: help
help: ## Prints this message
	@egrep -h '\s##\s' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

%/surelog:
	$(MAKE) -C $(SURELOG_DIR) release_with_python PREFIX=$(VENV_DIR)

%/verilator:
	cd $(VERILATOR_DIR); autoconf
	cd $(VERILATOR_DIR); ./configure --prefix=$(VENV_DIR)
	$(MAKE) -C $(VERILATOR) all
	$(MAKE) -C $(VERILATOR) install

deps: $(SURELOG_BIN) $(VERILATOR_BIN)
deps: ## Builds Surelog and Verilator binaries

%/.git:
	@$(eval IMPORT_DIR_REL := $(call bsg_rel_path,$(TOP),$(IMPORT_DIR)))
	@$(ECHO) "Fetching $(NUM_SUBMODULES) submodules"
	@$(GIT) submodule update \
		--progress \
		--init \
		--recursive \
		--recommend-shallow \
		--jobs $(NUM_SUBMODULES) \
		$(IMPORT_DIR_REL)

$(VENV_SCRIPT):
	@$(ECHO) "Creating python virtual environment"
	# Only tested on python3.12
	@python3.12 -m venv $(VENV_DIR)
	@$(PYTHON_RUN) -m pip install -r requirements.txt

setup: | $(SUBMODULE_GITS) $(VENV_SCRIPT)
setup: ## Setup the development environment

.PHONY: preview
preview: $(VENV_SCRIPT)
preview: ## Generates a preview for bsg_misc cores
	@$(ECHO) "Generating preview for bsg_misc cores"
	@$(PYTHON_RUN) $(TOP)/gen_core.py --cores-root=$(CORES_DIR) --preview

.PHONY: gen
gen: $(VENV_SCRIPT)
gen: ## Generates bsg_misc cores
	@$(ECHO) "Generating bsg_misc cores"
	@$(PYTHON_RUN) $(TOP)/gen_core.py --cores-root=$(CORES_DIR)

.PHONY: clean
clean: ## Cleans intermediate outputs
	@if [ -d "$(CORES_DIR)" ]; then \
		$(ECHO) "Removing $(CORES_DIR)"; \
		$(RMRF) $(CORES_DIR); \
	fi

.PHONY: bleach
bleach: clean
bleach: ## Destroys environment
	@if [ -d "$(VENV_DIR)" ]; then \
		$(ECHO) "Removing $(VENV_DIR)"; \
		$(RMRF) $(VENV_DIR); \
	fi
	@$(ECHO) "Deinitializing submodules"
	@$(GIT) submodule deinit -f $(IMPORT_DIR)
	
