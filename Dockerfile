# An image with the package installed: build it once, then run the command.
#
#   docker build -t hotel-market .
#   docker run --rm -v "$PWD:/work" hotel-market --seed 7 --template
#   docker run --rm -v "$PWD:/work" -e ANTHROPIC_API_KEY hotel-market --seed 7
#   docker run --rm --entrypoint python hotel-market -m pytest -p no:cacheprovider /app/tests
#
# The mount makes cache/, decisions.jsonl and hotel_market.duckdb land in the
# repository, as a local run would. The Makefile's image and docker-* targets run these.
FROM python:3.12-slim

# Install the package, pytest and ruff from a copy of the source.
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY kg ./kg
COPY kg_check.py ./
COPY customers ./customers
COPY sql ./sql
RUN pip install --no-cache-dir ".[dev]"

# Run from the mounted repository, so what a run writes lands there.
WORKDIR /work
ENTRYPOINT ["hotel-market"]
CMD ["--help"]
