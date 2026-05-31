# MK122 Fully Automated Quantitative Trading Autonomous System

MK122 is a fully automated quantitative trading autonomous system designed for the A-share stock market and ETFs. The current project starts from P0 infrastructure development, with the goal of first establishing a testable and scalable monorepo skeleton, and then gradually implementing data lake, signal generation, strategy, execution, risk control, meta-autonomy, and observability capabilities.

------

## Quick Start

```bash
uv sync
make test
make check
```

------

## Secrets Configuration

The Tushare token is not stored in the repository. Please set it as an environment variable in the development environment:

```bash
TUSHARE_TOKEN=your-token
```

You can also create a local secrets file based on `configs/secrets.local.yaml.example`; this file is already ignored by `.gitignore`.

------

## Data Ingestion Example

Fetch daily data from Tushare and write it to the local raw data directory:

```bash
uv run mk-data-fetch-daily --ts-code 000001.SZ --start-date 20240102 --end-date 20240105
```

By default, the output is stored in:

```
data/raw/tushare/daily/
```

The `data/` directory is used for local storage and is excluded via `.gitignore`.

------

## Additional Commands

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mk-learning-worker
uv run mkdocs build --strict
```
