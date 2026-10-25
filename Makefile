# Makefile for qgis-project (macOS only)
# Copy local.env.example to local.env before use (see README "Configuration").
# alidade reads local.env itself; the Makefile does not include it.

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

LOG ?= lint.log

.PHONY: help lint test clean

help:
	@echo "Targets:"
	@echo "  make dump DIR=project_dir          # finds .qgs or .qgz under DIR"
	@echo "  make build DIR=project_dir         # build .qgs or .lyrx based on project type"
	@echo "  make build-all DIR=project_dir     # force rebuild even if up to date"
	@echo "  make map DIR=project_dir           # render all maps to output/map_*.png"
	@echo "  make map DIR=project_dir MAP=id    # render one named map"
	@echo "  make extent DIR=project_dir        # print extent from QGIS-saved output/project.qgs"
	@echo "  make validate DIR=project_dir      # check all source/style paths exist"
	@echo "  make lint"
	@echo "  make publish DIR=project_dir         # publish layers to ArcGIS Online"
	@echo "  make publish DIR=project_dir MAP=id  # publish one named map"
	@echo "  make clean DIR=project_dir"

# Project targets (dump, build, map, publish, ...) shared with consuming
# projects; included after `help` so `help` stays the default target.
include alidade/alidade.mk

lint:
	> $(LOG)
	uv run black . 2>&1 | tee $(LOG)
	uv run flake8 . 2>&1 | tee -a $(LOG)
	uv run mypy . 2>&1 | tee -a $(LOG)

test:
	uv run pytest tests/ -x --tb=short

clean:
	@$(alidade_require_dir)
	rm -rf $(DIR)/output/
