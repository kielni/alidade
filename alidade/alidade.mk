# alidade.mk — make targets for alidade map projects.
#
# Include from a project Makefile:
#
#   include $(shell uv run alidade-mkinclude)
#
# Every target takes DIR=<map dir>; map and publish also take MAP=<map id>.
# Set ALIDADE to change how commands are run (default: `uv run`; set it to
# empty when alidade is installed on PATH).

ALIDADE ?= uv run

.PHONY: dump build build-all map extent validate publish

alidade_require_dir = if [ -z "$(DIR)" ]; then echo "Usage: make $@ DIR=map_dir"; exit 1; fi

dump:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-dump $(DIR)

build:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-build $(DIR)

build-all:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-build $(DIR) --force

map:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-map $(DIR) $(if $(MAP),--map $(MAP),)

extent:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-extent $(DIR)

validate:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-validate $(DIR)

publish:
	@$(alidade_require_dir)
	$(ALIDADE) alidade-publish $(DIR) $(if $(MAP),--map $(MAP),) --create-maps
