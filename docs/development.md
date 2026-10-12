# Development guide

## Environment

Use Python 3.11 or newer. From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Install optional media or inference dependencies only for work that needs
them:

```powershell
python -m pip install -e ".[search]"
python -m pip install -e ".[visual]"
python -m pip install -e ".[media]"
python -m pip install -e ".[models]"
```

FFmpeg is a system dependency, not installed by these Python extras. Confirm
`ffprobe` is on `PATH` before exercising media probing. The first indexing
run downloads Faster-Whisper `base` and CLIP `clip-ViT-B-32` into `data/models/`.

## Checks

```powershell
python -m pytest
python -m ruff check src tests eval
python -m ruff format --check tests eval
python -m mypy src
```

The API integration tests use deterministic test transcriber, frame sampler,
and image encoder doubles and do not download model weights. The formatter check covers `tests/` and `eval/`;
existing source files have formatting differences. Mypy currently reports
findings in existing source modules, so compare diagnostics when introducing
changes.

The Makefile provides aliases for common tasks, but GNU Make is not included
with Python and may not be available by default on Windows. The direct Python
commands above work without Make.

## Adding an extractor

1. Implement the `Extractor` contract in `src/vidsearch/extractors/`.
2. Return an `Evidence` tied to the `Segment` supplied to `run`.
3. Register the extractor explicitly with `ExtractorRegistry`.
4. Add unit tests for normal output, missing input, invalid outputs, and
   provider failures.
5. Add indexing and deletion coverage if the extractor's output is persisted.

There is no configuration-driven discovery yet. Do not add arbitrary imports
or class loading from user-controlled settings.

## Adding a storage adapter or endpoint

- Keep provider-specific code behind the metadata, vector, or queue
  boundaries.
- Define and test persistence, retrieval, isolation, and deletion behavior.
- Before exposing an endpoint, define request/response models, auth
  requirements, error contracts, and input limits.
- Add tests for successful multi-step behavior and rejected or unauthorized
  requests.
- Update the [API](api.md), [architecture](architecture.md), and
  [security](security.md) docs when behavior or trust boundaries change.

## Contribution practices

- Keep shared domain records in `core/schemas.py`.
- Keep input security checks in `core/security.py`.
- Keep unit fixtures synthetic and small.
- Never commit `.env`, credentials, private media, model weights, or raw
  benchmark datasets.
- Separate correctness tests from retrieval-quality evaluation.
