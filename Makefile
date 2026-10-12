# Sets the project up on a Mac or Linux machine (or WSL) and runs it.
#
#   make setup          create .venv and install the package, pytest and ruff into it
#   make test           run the tests (the slow 20-seed checks skipped)
#   make test-all       run every test, the slow checks included
#   make run SEED=7     run the simulation with the template reasons
#   make bench FIRST=1 LAST=3   benchmark the reviewers; make bench BENCH=--template runs it offline
#   make day SEED=7 DAY=20   run day 20 through the stored tables; make day-replay DAY=20 replays it
#   make image          build a Docker image instead; make docker-run SEED=7 runs it
#   make help           list every target
#
# Every target that needs the package runs the setup first, so `make test`
# works on a fresh clone. PYTHON picks the interpreter that creates the
# virtual environment: make setup PYTHON=python3.12

# A local .env (never committed) may hold ANTHROPIC_API_KEY and ANTHROPIC_WORKSPACE_ID.
-include .env
export ANTHROPIC_API_KEY ANTHROPIC_WORKSPACE_ID

PYTHON ?= python3
VENV   ?= .venv
IMAGE  ?= hotel-market
SEED   ?= 7
DAY    ?= 20
FIRST  ?= 1
LAST   ?= 20

BIN   := $(VENV)/bin
STAMP := $(VENV)/.installed

.DEFAULT_GOAL := help
.PHONY: help setup test test-all lint check run live live-audit replay sweep bench day day-replay \
        clean clean-run clean-all image docker-test docker-run docker-live

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  make %-10s %s\n", $$1, $$2}'

setup: $(STAMP) ## Create .venv and install the package, pytest and ruff into it

$(BIN)/python:
	@$(PYTHON) -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null \
		|| { echo "Python 3.11 or later is needed. Point PYTHON at one: make setup PYTHON=python3.12"; exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip

# Reinstalls when pyproject.toml changes; the venv itself is only a prerequisite for existing.
$(STAMP): pyproject.toml | $(BIN)/python
	$(BIN)/python -m pip install -e ".[dev]"
	@touch $@

test: $(STAMP) ## Run the tests (they run offline; the slow 20-seed checks are skipped)
	$(BIN)/python -m pytest

test-all: $(STAMP) ## Run every test, the slow 20-seed checks included (about two minutes)
	$(BIN)/python -m pytest --slow

lint: $(STAMP) ## Run ruff: the checks, and the formatter as a check
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

check: lint test ## Lint, then test

run: $(STAMP) ## Run seed SEED with the template reasons (no API key needed)
	$(BIN)/hotel-market --seed $(SEED) --template

live: $(STAMP) ## Run seed SEED with the model writing the reasons (needs ANTHROPIC_API_KEY)
	@test -n "$$ANTHROPIC_API_KEY" || { echo "ANTHROPIC_API_KEY is not set, so the run would fall back to the template."; exit 1; }
	$(BIN)/hotel-market --seed $(SEED)

live-audit: $(STAMP) ## Run seed SEED with the model, measured, then print every reason, every declined plan and every number not in its request (needs ANTHROPIC_API_KEY, here or in .env)
	@test -n "$$ANTHROPIC_API_KEY" || { echo "ANTHROPIC_API_KEY is not set, so the run would fall back to the template."; exit 1; }
	$(BIN)/python scripts/live_audit.py --seed $(SEED)

replay: $(STAMP) ## Print day DAY of seed SEED from the cache
	$(BIN)/hotel-market --seed $(SEED) --replay $(DAY)

sweep: $(STAMP) ## Run seeds FIRST to LAST with the template
	$(BIN)/hotel-market --seeds $(FIRST) $(LAST)

bench: $(STAMP) ## Benchmark the reviewers on seeds FIRST to LAST: the template, the oracle and each model (needs ANTHROPIC_API_KEY; BENCH=--template runs offline)
	$(BIN)/hotel-market bench --seeds $(FIRST) $(LAST) $(BENCH)

day: $(STAMP) ## Run day DAY of seed SEED through the stored tables (hotel_market.duckdb), from day 0 if the file is new
	$(BIN)/hotel-market run-day --seed $(SEED) --as-of $(DAY) $(if $(wildcard hotel_market.duckdb),,--from 0) --template

day-replay: $(STAMP) ## Rebuild day DAY's plans from the stored tables alone and print its queue
	$(BIN)/hotel-market replay --as-of $(DAY)

clean: ## Remove Python and test leftovers
	rm -rf .pytest_cache .ruff_cache src/*.egg-info
	find src tests -name __pycache__ -type d -exec rm -rf {} +

clean-run: ## Remove what a run writes: cache/ (the model's answers), decisions.jsonl, calls.jsonl, schedule.csv, hotel_market.duckdb
	rm -rf cache decisions.jsonl calls.jsonl schedule.csv hotel_market.duckdb hotel_market.duckdb.wal

clean-all: clean clean-run ## Also remove .venv
	rm -rf $(VENV)

# The container route: the same commands, with Docker instead of a .venv.
# The mount makes cache/ and decisions.jsonl land here, as a local run would.
image: ## Build the Docker image (needs Docker)
	docker build -t $(IMAGE) .

docker-test: image ## Run the tests inside the image
	docker run --rm --entrypoint python $(IMAGE) -m pytest -p no:cacheprovider /app/tests

docker-run: image ## Run seed SEED in a container with the template reasons
	docker run --rm -v "$(CURDIR):/work" $(IMAGE) --seed $(SEED) --template

docker-live: image ## The same with the model writing the reasons (needs ANTHROPIC_API_KEY)
	@test -n "$$ANTHROPIC_API_KEY" || { echo "ANTHROPIC_API_KEY is not set, so the run would fall back to the template."; exit 1; }
	docker run --rm -e ANTHROPIC_API_KEY -v "$(CURDIR):/work" $(IMAGE) --seed $(SEED)
