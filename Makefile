# Sets the project up on a Mac or Linux machine (or WSL) and runs it.
#
#   make setup          create .venv and install the package, pytest and ruff into it
#   make test           run the tests (the nine slow tests skipped)
#   make test-all       run every test, the nine slow tests included (about 20 minutes)
#   make run SEED=7     run the simulation with the template reasons
#   make bench FIRST=1 LAST=3   benchmark the reviewers; make bench BENCH=--template runs it offline
#   make day SEED=7 DAY=20   run day 20 through the stored tables; make day-replay DAY=20 replays it
#   make demo SEED=7     write demo.duckdb from the recorded run and start the demo page (installs streamlit)
#   make screenshots     screenshot the demo page at 1440 by 900, in both states, and fail if a page is taller than the window
#   make image          build the Docker image hotel-market:py3.12; make docker-run SEED=7 runs it
#   make image PYTHON=3.11   the same on another Python, tagged hotel-market:py3.11
#   make help           list every target
#
# Every target that needs the package runs the setup first, so `make test`
# works on a fresh clone. PYTHON picks the interpreter that creates the
# virtual environment: make setup PYTHON=python3.12

# A local .env (never committed) may hold ANTHROPIC_API_KEY and ANTHROPIC_WORKSPACE_ID. Make
# keeps the quotes of a quoted value, which the API then rejects, so they are stripped here.
-include .env
ANTHROPIC_API_KEY := $(strip $(subst ",,$(subst ',,$(ANTHROPIC_API_KEY))))
ANTHROPIC_WORKSPACE_ID := $(strip $(subst ",,$(subst ',,$(ANTHROPIC_WORKSPACE_ID))))
export ANTHROPIC_API_KEY ANTHROPIC_WORKSPACE_ID

PYTHON ?= python3
VENV   ?= .venv
IMAGE  ?= hotel-market
# A PYTHON that is a version, such as 3.11, picks the image's base Python; any other
# PYTHON is the interpreter for the venv, and the image keeps the Dockerfile's default.
IMAGE_PYTHON := $(if $(filter 3.%,$(PYTHON)),$(PYTHON),3.12)
TAG    := $(IMAGE):py$(IMAGE_PYTHON)
SEED   ?= 7
DAY    ?= 20
FIRST  ?= 1
LAST   ?= 20

BIN   := $(VENV)/bin
STAMP := $(VENV)/.installed

.DEFAULT_GOAL := help
.PHONY: help setup test test-all lint check run live live-audit replay sweep bench day day-replay \
        demo screenshots clean clean-run clean-all image docker-test docker-run docker-live

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

test: $(STAMP) ## Run the tests (they run offline; the nine slow tests are skipped)
	$(BIN)/python -m pytest

test-all: $(STAMP) ## Run every test, the nine slow tests included: each a 20-seed sweep or several, about 20 minutes on a laptop
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

demo: $(STAMP) ## Write demo.duckdb for seed SEED from the recorded live run and start the demo page (no API key; installs the demo extra)
	@$(BIN)/python -c 'import streamlit' 2>/dev/null || $(BIN)/python -m pip install -e ".[demo]"
	$(BIN)/hotel-market demo-data --seed $(SEED) --out demo.duckdb
	@echo "Open http://localhost:8501 in a browser (Streamlit prints another port if that one is taken)."
	HOTEL_MARKET_DEMO_FILE=demo.duckdb $(BIN)/streamlit run src/hotel_market/demo_page.py --server.headless true --browser.gatherUsageStats false

screenshots: $(STAMP) ## Open the demo page at 1440 by 900 in a Chromium-based browser, save six screenshots under screenshots/ (three pages, the end-of-run result off and on), and fail if one is taller than the window
	@$(BIN)/python -c 'import streamlit' 2>/dev/null || $(BIN)/python -m pip install -e ".[demo]"
	@test -f demo.duckdb || $(BIN)/hotel-market demo-data --seed $(SEED) --out demo.duckdb
	$(BIN)/python scripts/demo_screenshots.py --file demo.duckdb --out screenshots

clean: ## Remove Python and test leftovers
	rm -rf .pytest_cache .ruff_cache src/*.egg-info
	find src tests -name __pycache__ -type d -exec rm -rf {} +

clean-run: ## Remove what a run writes: cache/ (the model's answers), decisions.jsonl, calls.jsonl, schedule.csv, hotel_market.duckdb, demo.duckdb, screenshots/
	rm -rf cache decisions.jsonl calls.jsonl schedule.csv hotel_market.duckdb hotel_market.duckdb.wal demo.duckdb demo.duckdb.wal screenshots

clean-all: clean clean-run ## Also remove .venv
	rm -rf $(VENV)

# The container route: the same commands, with Docker instead of a .venv.
# The mount makes cache/ and decisions.jsonl land here, as a local run would.
image: ## Build the Docker image, tagged hotel-market:py3.12 (needs Docker); PYTHON=3.11 builds on that Python
	docker build --build-arg PYTHON=$(IMAGE_PYTHON) -t $(TAG) .

docker-test: image ## Run the tests inside the image, from its copy of the repository
	docker run --rm --entrypoint python -w /app $(TAG) -m pytest -p no:cacheprovider tests

docker-run: image ## Run seed SEED in a container with the template reasons
	docker run --rm -v "$(CURDIR):/work" $(TAG) --seed $(SEED) --template

docker-live: image ## The same with the model writing the reasons (needs ANTHROPIC_API_KEY)
	@test -n "$$ANTHROPIC_API_KEY" || { echo "ANTHROPIC_API_KEY is not set, so the run would fall back to the template."; exit 1; }
	docker run --rm -e ANTHROPIC_API_KEY -v "$(CURDIR):/work" $(TAG) --seed $(SEED)
