# Makefile for qgis-project (macOS only)
# Copy local.env.example to local.env and set QGIS before use.

-include local.env

RUN := uv run python

.PHONY: help dump build build-all capture validate lint clean

help:
	@echo "Targets:"
	@echo "  make dump DIR=project_dir      # finds .qgs or .qgz under DIR"
	@echo "  make build DIR=project_dir"
	@echo "  make build-all DIR=project_dir  # force rebuild even if up to date"
	@echo "  make capture DIR=project_dir   # sync extent from QGIS-saved output/project.qgs to project.py"
	@echo "  make validate DIR=project_dir  # check all source/style paths exist"
	@echo "  make lint"
	@echo "  make clean DIR=project_dir"

dump:
	@if [ -z "$(DIR)" ]; then echo "Usage: make dump DIR=project_dir"; exit 1; fi
	$(RUN) alidade/dump.py $(DIR)

build:
	@if [ -z "$(DIR)" ]; then echo "Usage: make build DIR=project_dir"; exit 1; fi
	$(RUN) alidade/build.py $(DIR)

build-all:
	@if [ -z "$(DIR)" ]; then echo "Usage: make build-all DIR=project_dir"; exit 1; fi
	$(RUN) alidade/build.py $(DIR) --force

capture:
	@if [ -z "$(DIR)" ]; then echo "Usage: make capture DIR=project_dir"; exit 1; fi
	$(RUN) alidade/capture.py $(DIR)

validate:
	@if [ -z "$(DIR)" ]; then echo "Usage: make validate DIR=project_dir"; exit 1; fi
	$(RUN) alidade/validate.py $(DIR)

lint:
	uv run black .
	uv run flake8 .

clean:
	@if [ -z "$(DIR)" ]; then echo "Usage: make clean DIR=project_dir"; exit 1; fi
	rm -rf $(DIR)/output/
