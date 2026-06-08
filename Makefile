# Makefile for qgis-project (macOS only)
# Copy local.env.example to local.env and set QGIS before use.

-include local.env
export ARCGIS_WORKSPACE_ROOT

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

LOG ?= lint.log

.PHONY: help dump build build-all map extent validate lint publish clean

help:
	@echo "Targets:"
	@echo "  make dump DIR=project_dir          # finds .qgs or .qgz under DIR"
	@echo "  make build DIR=project_dir         # build .qgs or .lyrx based on project type"
	@echo "  make build-all DIR=project_dir     # force rebuild even if up to date"
	@echo "  make map DIR=project_dir           # re-render map.png unconditionally"
	@echo "  make extent DIR=project_dir        # print extent from QGIS-saved output/project.qgs"
	@echo "  make validate DIR=project_dir      # check all source/style paths exist"
	@echo "  make lint"
	@echo "  make publish DIR=project_dir         # publish layers to ArcGIS Online"
	@echo "  make publish DIR=project_dir MAP=id  # publish one named map"
	@echo "  make clean DIR=project_dir"

dump:
	@if [ -z "$(DIR)" ]; then echo "Usage: make dump DIR=project_dir"; exit 1; fi
	uv run alidade-dump $(DIR)

build:
	@if [ -z "$(DIR)" ]; then echo "Usage: make build DIR=project_dir"; exit 1; fi
	uv run alidade-build $(DIR)

build-all:
	@if [ -z "$(DIR)" ]; then echo "Usage: make build-all DIR=project_dir"; exit 1; fi
	uv run alidade-build $(DIR) --force

map:
	@if [ -z "$(DIR)" ]; then echo "Usage: make map DIR=project_dir"; exit 1; fi
	uv run alidade-map $(DIR)

extent:
	@if [ -z "$(DIR)" ]; then echo "Usage: make extent DIR=project_dir"; exit 1; fi
	uv run alidade-extent $(DIR)

validate:
	@if [ -z "$(DIR)" ]; then echo "Usage: make validate DIR=project_dir"; exit 1; fi
	uv run alidade-validate $(DIR)

lint:
	> $(LOG)
	uv run black . 2>&1 | tee $(LOG)
	uv run flake8 . 2>&1 | tee -a $(LOG)
	uv run mypy . 2>&1 | tee -a $(LOG)

publish:
	@if [ -z "$(DIR)" ]; then echo "Usage: make publish DIR=project_dir [MAP=map_id]"; exit 1; fi
	uv run python -m alidade.publish_arcgis $(DIR) $(if $(MAP),--map $(MAP),) --create-maps

clean:
	@if [ -z "$(DIR)" ]; then echo "Usage: make clean DIR=project_dir"; exit 1; fi
	rm -rf $(DIR)/output/
