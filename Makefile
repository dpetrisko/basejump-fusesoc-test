###################################################
# Calculated Variables
###################################################
TOP ?= $(shell git rev-parse --show-toplevel)
NUM_SUBMODULES ?=  $(shell ls $(IMPORT_DIR)/ | wc -l | xargs)

###################################################
# Required Executables
###################################################
AWK ?= awk
AUTOCONF ?= autoconf
CD ?= cd
ECHO ?= $(if $(shell which gecho 2>/dev/null),gecho,echo)
EGREP ?= egrep
FUSESOC ?= fusesoc
GIT ?= git
PYTHON ?= python
REALPATH ?= $(if $(shell which grealpath 2>/dev/null),grealpath,realpath)
RMRF ?= rm -rf
SORT ?= sort
TR ?= $(if $(shell which gtr 2>/dev/null),gtr,tr)

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
SURELOG_DIR ?= $(IMPORT_DIR)/Surelog
VERILATOR_DIR ?= $(IMPORT_DIR)/verilator

###################################################
# Commands
###################################################
VENV_SCRIPT ?= $(VENV_DIR)/bin/activate
VENV_ACTIVATE ?= source $(VENV_SCRIPT)
PYTHON_RUN ?= $(VENV_ACTIVATE) && python

SURELOG_BIN ?= $(VENV_DIR)/bin/surelog
VERILATOR_BIN ?= $(VENV_DIR)/bin/verilator

###################################################
# Helper Targets
###################################################
%/surelog: | $(VENV_SCRIPT) $(SURELOG_DIR)/.git
	@$(CD) $(SURELOG_DIR); $(VENV_ACTIVATE) && \
		$(MAKE) release_with_python PREFIX=$(VENV_DIR)

%/verilator: | $(VENV_SCRIPT) $(VERILATOR_DIR)/.git
	@$(CD) $(VERILATOR_DIR); $(VENV_ACTIVATE) && \
		$(AUTOCONF); \
		./configure --prefix=$(VENV_DIR); \
		$(MAKE) all; \
		$(MAKE) install

%/.git: | $(VENV_SCRIPT)
	@$(GIT) submodule update \
		--progress \
		--init \
		--recursive \
		--recommend-shallow \
		$(@D)

%/bin/activate:
	@$(ECHO) "Creating python virtual environment"
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PYTHON_RUN) -m pip install -r requirements.txt

###################################################
# User Targets
###################################################
.DEFAULT_GOAL: help
.PHONY: help
help: ## Prints this message
	@$(EGREP) -h '\s##\s' $(MAKEFILE_LIST) \
		| $(SORT) \
		| $(AWK) 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Setup the development environment
setup:
	@$(MAKE) $(VENV_SCRIPT)
	@$(MAKE) $(SURELOG_BIN)
	@$(MAKE) $(VERILATOR_BIN)

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

.PHONY: update
update: $(VENV_SCRIPT)
update: ## Updates the fusesoc library
	@$(ECHO) "Updating fusesoc library"
	@$(FUSESOC) library update

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
	
