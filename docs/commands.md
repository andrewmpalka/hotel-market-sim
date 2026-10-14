# Commands

Every command of the repository, with its one-line comment. The README keeps the three that start a demo.

Python 3.11 or later, from the repository root:

    pip install -e ".[dev]"                  # the package, its dependencies, pytest and ruff
    python -m pytest                         # the tests, offline; the nine slow tests are skipped
    python -m pytest --slow                  # every test; nine slow tests, about twenty minutes
    ruff check . && ruff format --check .    # the linter and the formatter, as a check
    python kg_check.py                       # the knowledge graph against the code

    hotel-market --seed 7 --template         # both runs, decisions.jsonl, the daily queues, the summary
    hotel-market --seed 7                    # the same, the model writing the reasons (needs ANTHROPIC_API_KEY)
    hotel-market --seed 7 --replay 20        # day 20's queue again, without a model call
    hotel-market --seeds 1 20                # seeds 1 to 20: mean and range of the contribution change
    hotel-market --seeds 1 20 --elasticity true --elasticity learn:1.0 --cautious   # one arm per mode
    hotel-market --seed 7 --customer customers/demo.toml --target revenue           # another market or target
    hotel-market run-day --seed 7 --as-of 20 --from 0   # days 0 to 20, one day at a time, through stored tables
    hotel-market replay --as-of 20                      # day 20's plans again, from the stored tables alone
    python scripts/live_audit.py --seed 7               # a live run, every model call measured, then audited
    hotel-market demo-data --seed 7                     # demo.duckdb: the stored tables and the demo page's tables, reasons from the recorded run
    pip install -e ".[demo]" && HOTEL_MARKET_DEMO_FILE=demo.duckdb streamlit run src/hotel_market/demo_page.py
                                                        # the read-only demo page over that file; no API key
    python scripts/demo_screenshots.py                  # the page at 1440 by 900 in a Chromium-based browser: three pages, each with the end-of-run result off and on, and a failure if one is taller
    hotel-market bench --seeds 1 20 --template          # the template and the oracle reviewer, in three modes, offline
    hotel-market bench --seeds 1 3                      # the same with each Claude model reviewing (needs ANTHROPIC_API_KEY)
    hotel-market bench --seeds 1 20 --template --demand-bias 0.9 --elasticity true --elasticity learn:1.0
                                                        # the simulator's demand times 0.9, which the agent never sees
    hotel-market bench --seeds 1 20 --template --react  # competitors follow the hotels' rate changes, three days later
    hotel-market bench --seeds 1 20 --template --react --market-elasticity 0.5
                                                        # the market's demand answers the comp median's level; the agent is told the value
    hotel-market --seeds 1 20 --churn                   # the airline files weekly revisions below the threshold
    hotel-market --seeds 1 20 --scenario upgauge        # another set of air-schedule filings
    python scripts/median_path.py --seed 7 --react --hotel convention --stays 45 48 --days 9 15
                                                        # a comp median's path next to the hotel's rate

With make, on a Mac or Linux machine:

    make setup                 # create .venv and install the package, pytest and ruff into it
    make test                  # the tests; make lint runs ruff
    make test-all              # every test; nine slow tests, about twenty minutes
    make run SEED=7            # the template run; make live SEED=7 uses the model
    make bench FIRST=1 LAST=3  # the reviewers benchmarked; make bench BENCH=--template runs it offline
    make day SEED=7 DAY=20     # a day through the stored tables; make day-replay DAY=20 replays it
    make demo SEED=7           # write demo.duckdb from the recorded run and start the demo page
    make screenshots           # screenshot the demo page at 1440 by 900, in both states, and fail if a page is taller than the window
    make help                  # every target

With Docker:

    docker build -t hotel-market:py3.12 .                        # --build-arg PYTHON=3.11 for another Python
    docker run --rm -v "$PWD:/work" hotel-market:py3.12 --seed 7 --template
    docker run --rm -v "$PWD:/work" -e ANTHROPIC_API_KEY hotel-market:py3.12 --seed 7
    docker run --rm --entrypoint python -w /app hotel-market:py3.12 -m pytest -p no:cacheprovider tests
