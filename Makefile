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
VENV_DIR ?= $(TOP)/.venv
BASEJUMP_CORES_DIR ?= $(TOP)/basejump_stl_cores
BASEJUMP_REF_DIR ?= $(TOP)/basejump_stl_ref
FUSESOC_CONF ?= $(TOP)/fusesoc.conf

###################################################
# Commands
###################################################
VENV_SCRIPT ?= $(VENV_DIR)/bin/activate
VENV_ACTIVATE ?= source $(VENV_SCRIPT)
PYTHON_RUN ?= $(VENV_ACTIVATE) && python

###################################################
# Helper Targets
###################################################
%/basejump_stl_ref:
	@$(eval BASEJUMP_STL_URL := "https://github.com/bespoke-silicon-group/basejump_stl.git")
	@$(eval BASEJUMP_STL_TAG := "v0.0.1")
	@$(ECHO) "Cloning BaseJump STL"
	@$(GIT) clone -b $(BASEJUMP_STL_TAG) --single-branch $(BASEJUMP_STL_URL) $@

%/bin/activate: $(BASEJUMP_REF_DIR)
	@$(ECHO) "Creating python virtual environment"
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PYTHON_RUN) -m pip install -r requirements.txt

$(FUSESOC_CONF):
	@$(ECHO) "Adding fusesoc library"
	@$(FUSESOC) library add $(BASEJUMP_CORES_DIR)

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
setup: | $(VENV_SCRIPT)
	
.PHONY: preview
preview: | $(VENV_SCRIPT)
preview: ## Generates a preview for basejump_stl cores
	@$(ECHO) "Generating preview for basejump_stl cores"
	@$(PYTHON_RUN) $(TOP)/gen_core.py --basejump-stl-root=$(BASEJUMP_REF_DIR) --cores-root=$(BASEJUMP_CORES_DIR) --preview

.PHONY: gen
gen: | $(VENV_SCRIPT)
gen: ## Generates basejump_stl cores
	@$(ECHO) "Generating basejump_stl cores"
	@$(PYTHON_RUN) $(TOP)/gen_core.py --basejump-stl-root=$(BASEJUMP_REF_DIR) --cores-root=$(BASEJUMP_CORES_DIR)

.PHONY: init
init: | $(VENV_SCRIPT)
init: ## Initializes the fusesoc library
	@$(ECHO) "Initializing fusesoc library"
	@$(FUSESOC) library add $(BASEJUMP_CORES_DIR)

.PHONY: update
update: | $(VENV_SCRIPT) $(FUSESOC_CONF)
update: ## Updates the fusesoc library
	@$(ECHO) "Updating fusesoc library"
	@$(FUSESOC) library update

.PHONY: clean
clean: ## Cleans intermediate outputs
	@if [ -d "$(BASEJUMP_CORES_DIR)" ]; then \
		$(ECHO) "Removing $(BASEJUMP_CORES_DIR)"; \
		$(RMRF) $(BASEJUMP_CORES_DIR); \
	fi

.PHONY: bleach
bleach: clean
bleach: ## Destroys environment
	@if [ -d "$(VENV_DIR)" ]; then \
		$(ECHO) "Removing $(VENV_DIR)"; \
		$(RMRF) $(VENV_DIR); \
	fi
	@if [ -d "$(BASEJUMP_REF_DIR)" ]; then \
		$(ECHO) "Removing $(BASEJUMP_REF_DIR)"; \
		$(RMRF) $(BASEJUMP_REF_DIR); \
	fi
	@if [ -f "$(FUSESOC_CONF)" ]; then \
		$(ECHO) "Removing $(FUSESOC_CONF)"; \
		$(RMRF) $(FUSESOC_CONF); \
	fi
	
