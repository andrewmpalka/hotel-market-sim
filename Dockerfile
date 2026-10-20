# An image with the package installed: build it once, then run the command.
#
#   docker build -t hotel-market:py3.12 .                           # the default Python
#   docker build --build-arg PYTHON=3.11 -t hotel-market:py3.11 .   # another Python
#   docker run --rm -v "$PWD:/work" hotel-market:py3.12 --seed 7 --template
#   docker run --rm -v "$PWD:/work" -e ANTHROPIC_API_KEY hotel-market:py3.12 --seed 7
#   docker run --rm --entrypoint python -w /app hotel-market:py3.12 -m pytest -p no:cacheprovider tests
#
# The mount makes cache/, decisions.jsonl and hotel_market.duckdb land in the
# repository, as a local run would. The Makefile's image and docker-* targets run
# these, and make image PYTHON=3.11 picks the base image.
ARG PYTHON=3.12
FROM python:${PYTHON}-slim

# Install the package, pytest and ruff from a copy of the source. The tests also read
# the scripts, the docs, the Makefile, the demo page's theme and this file, so the copy
# carries them too.
WORKDIR /app
COPY pyproject.toml README.md Makefile Dockerfile kg_check.py ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY kg ./kg
COPY docs ./docs
COPY customers ./customers
COPY sql ./sql
COPY .streamlit ./.streamlit
RUN pip install --no-cache-dir ".[dev]"
# The installed package has no checkout to find the demo market in, so the variable names it.
ENV HOTEL_MARKET_CUSTOMER=/app/customers/demo.toml

# Run from the mounted repository, so what a run writes lands there.
WORKDIR /work
ENTRYPOINT ["hotel-market"]
CMD ["--help"]
