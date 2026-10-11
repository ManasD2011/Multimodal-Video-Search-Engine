PYTHON ?= python
PIP ?= $(PYTHON) -m pip
VIDEO ?=
EVAL_GROUND_TRUTH ?= eval/datasets/custom/queries.jsonl
EVAL_PREDICTIONS ?=
EVAL_OUTPUT_DIR ?= eval/results

.PHONY: help install up test lint format-check typecheck eval ingest

help:
	@echo "Targets: install, up, test, lint, format-check, typecheck, eval, ingest"

install:
	$(PIP) install -e ".[dev]"

up:
	$(PYTHON) -m uvicorn --factory vidsearch.api.main:create_app --reload

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests eval

format-check:
	$(PYTHON) -m ruff format --check tests eval

typecheck:
	$(PYTHON) -m mypy src

ifeq ($(strip $(EVAL_PREDICTIONS)),)
eval:
	@echo "Set EVAL_PREDICTIONS to a ranked prediction JSONL file."
	@exit 2
else
eval:
	$(PYTHON) -m eval.run_eval --ground-truth "$(EVAL_GROUND_TRUTH)" --predictions "$(EVAL_PREDICTIONS)" --output-dir "$(EVAL_OUTPUT_DIR)"
endif

ingest:
	$(PYTHON) -c "raise SystemExit('Ingestion is not wired yet; implement the CLI/API before running ingestion.')"
