# Vidsearch

**Search video by what happens, what is said, and what appears on screen.**

Vidsearch is a Python project scaffold for multimodal video search. The
intended system turns videos into timestamped segments, extracts evidence
from multiple modalities, indexes that evidence, and returns ranked moments
for a natural-language query.

> **Project status: local development prototype.** The local API stores videos,
> transcribes speech on the CPU, and samples frames for local CLIP image-text
> search. YouTube video URLs can also be imported. OCR, object detection,
> audio-event search, distributed workers, authentication, and production
> storage are not implemented.

## The idea

```text
Video library
    -> validate and inspect media
    -> split into timestamped segments
    -> extract visual, speech, caption, OCR, object, and audio evidence
    -> index evidence
    -> search, fuse rankings, and return matching timestamps
```

The diagram below shows the intended system and marks unfinished
integrations. It is a design map, not a claim that every connection currently
runs.

[![Vidsearch architecture: ingestion, evidence extraction, indexing, and search](docs/assets/application-architecture.svg)](docs/architecture.md)

For module-level interactions and the full editable diagrams, see
[Architecture](docs/architecture.md).

## What is implemented today

| Area | Current state |
| --- | --- |
| Shared domain | Dataclasses for `Segment`, `Evidence`, `Query`, `SearchHit`, and `SearchResult` |
| Local media safety | Allowed-root path validation, URL validation helper, and byte-size checks |
| Media inspection | `ffprobe` wrapper that enforces file-size and duration limits |
| Segmentation | Pure-Python fixed time windows and adjacent-window merging |
| Extractor architecture | Base contract and explicit plugin registry; speech transcription uses Faster-Whisper, visual search uses CLIP |
| Retrieval | BM25 over persisted transcripts plus local CLIP visual similarity |
| Ranking | Reciprocal-rank fusion and temporal merge/selection utilities |
| API | Local upload, YouTube URL import, background visual/speech indexing, SQLite-backed library and evidence metadata, media playback, deletion, health, and search routes |
| Frontend | React/Vite library, local video preview, file and YouTube URL imports, indexing status, and visual/speech search |
| Workers | Queue and task backends are not implemented |
| Vector and SQL persistence | Interfaces/dependencies exist; durable adapters are not connected |
| Tests | Backend API integration tests and frontend API-client tests; remaining planned suites still include placeholders |
| Evaluation | JSONL-based ranking and temporal metrics, annotation normalizers, ablation comparison, and a performance utility |

The key boundary to keep in mind: an installed package or a declared
environment variable does not mean its service is connected. See
[Project status](docs/README.md) for details and
[the annotated source tree](docs/project-structure.md) for file ownership.

## Get started

### Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer and npm (for the frontend)
- `ffprobe` (optional; needed only for media probing)

### Install dependencies

From the repository root, create and activate a virtual environment. These
commands install the backend development tools, API upload support,
evaluation config support, speech/YouTube search, and local visual-search
dependencies.

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,eval,search,visual]"
```

**macOS or Linux**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,eval,search,visual]"
```

Install frontend dependencies in a second terminal:

```bash
cd frontend
npm ci
```

Optional dependency groups add other media processing and model libraries:

```bash
python -m pip install -e ".[media,models]"
```

The `search` extra installs Faster-Whisper and yt-dlp; `visual` installs
OpenCV and Sentence Transformers. The first indexing run downloads the
Faster-Whisper `base` model and CLIP `clip-ViT-B-32` into `data/models/`.
Visual embeddings and transcripts remain local. URL imports accept only public HTTPS YouTube URLs
and enforce the configured size and duration limits. Import videos only when
you have the rights and permission to use them.

### Configure and run the application

The backend reads supported settings from process environment variables; it
does not load `.env` automatically. Defaults are suitable for a local demo.
For example, in PowerShell:

```powershell
$env:VIDSEARCH_DATA_DIR = "data"
$env:VIDSEARCH_MAX_VIDEO_BYTES = "2000000000"
```

See the [configuration guide](docs/configuration.md) for supported settings.
Do not put real credentials in `.env.example` or commit a `.env` file.

Start the backend from the repository root:

```powershell
python -m uvicorn --factory vidsearch.api.main:create_app --app-dir src --reload
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies API requests to
`http://127.0.0.1:8000`. Uploaded or imported videos are transcribed and
sampled for visual search in the background; their library status changes to
**Indexed** when processing completes. The API has no authentication; keep it on a trusted local
machine. See the [API guide](docs/api.md) for endpoint details.

Check that the backend is running:

**Windows PowerShell**

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

If you are using Command Prompt, Git Bash, or macOS/Linux, use `curl` instead:

```text
curl http://127.0.0.1:8000/healthz
```

Stop either development server with `Ctrl+C`.

## Checks and tests

Run backend checks from the repository root after activating the virtual
environment:

```powershell
# All backend tests
python -m pytest

# Select individual test suites
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/security

# Coverage report
python -m pytest --cov=vidsearch --cov-report=term-missing

# Lint, formatting, and static types
python -m ruff check src tests eval
python -m ruff format --check src tests eval
python -m mypy src
```

Run frontend checks from the `frontend/` directory:

```powershell
# ESLint
npm run lint

# TypeScript check and production Vite build
npm run build

# Frontend unit/component tests (Vitest)
npm test

# Browser end-to-end tests (Playwright)
npx playwright install chromium
npm run test:e2e
```

The Playwright test starts its own Vite server and mocks the API responses, so
it does not require the backend to be running. Install the browser once per
machine; the normal test command can then be repeated without the install
step.

To run every local check together, execute the backend commands above, then
run `npm run lint`, `npm run build`, and `npm test` in `frontend/`. The
Playwright E2E suite is a separate browser check. Some backend unit/security
cases are still scaffold placeholders and will be reported as skipped; the
API integration tests exercise the local upload/library endpoints when the
`api` extra is installed.

### Security and pre-commit checks

The security workflow runs Bandit, `pip-audit`, Trivy, and Gitleaks on GitHub.
To run the Python scanners locally, install Bandit and pip-audit into the
active virtual environment, then run:

```powershell
python -m pip install bandit pip-audit
bandit -r src -ll
pip-audit
```

Trivy and Gitleaks are standalone tools that must be installed separately:

```powershell
trivy fs --scanners vuln,misconfig --severity CRITICAL,HIGH --ignore-unfixed .
gitleaks detect --source . --verbose
```

Run the configured pre-commit hooks across the repository with:

```powershell
pre-commit run --all-files
```

These scanners may report dependency or source issues that need triage; a
clean run is not a substitute for reviewing the
[security guide](docs/security.md).

## GitHub Actions

The workflows in [`.github/workflows/`](.github/workflows/) run on pushes and
pull requests:

- `ci.yml`: Ruff lint and formatting, mypy, unit tests, and integration tests.
- `security.yml`: Bandit, `pip-audit`, Trivy filesystem scanning, and Gitleaks;
  it also runs weekly.
- `eval-smoke.yml`: checks evaluation metrics against the synthetic example
  annotation. It verifies evaluator behavior, not retrieval/model quality.

## Evaluate a search system

The evaluator compares your own ranked prediction export against query
annotations. It does not run inference or download a benchmark dataset.
Prediction records should look like:

```json
{"query_id":"q1","results":[{"video_id":"video-1","start":2.4,"end":5.0,"score":0.91}]}
```

Run evaluation after preparing a predictions JSONL file:

```powershell
python -m eval.run_eval `
  --ground-truth eval/datasets/custom/queries.jsonl `
  --predictions path\to\predictions.jsonl `
  --output-dir eval/results
```

The checked-in query is synthetic example data, not a benchmark. Metrics
include Recall@k, MRR, MeanIoU, and rank-one temporal recall at configured
IoU thresholds. Read the [evaluation guide](docs/evaluation.md) for data
formats, annotation adapters, ablations, and performance measurements.

## Find your way around

| If you want to... | Start here |
| --- | --- |
| Understand the whole design | [Architecture and diagrams](docs/architecture.md) |
| Find a module or file | [Annotated project structure](docs/project-structure.md) |
| Check available settings | [Configuration reference](docs/configuration.md) |
| Implement an API endpoint | [API status and contract direction](docs/api.md) |
| Add an extractor or storage adapter | [Development guide](docs/development.md) |
| Run retrieval-quality experiments | [Evaluation guide](docs/evaluation.md) |
| Review trust boundaries and release risks | [Security guide](docs/security.md) |
| Browse every guide | [Documentation index](docs/README.md) |

## Project layout

```text
src/vidsearch/   Python application: core, ingestion, extractors, indexing,
                 query planning, retrieval, API, and workers
tests/           Behavior and security test scaffolds
eval/            Offline quality metrics and benchmark utilities
docs/            Architecture, API, configuration, security, and dev guides
```

The `frontend/` directory contains the React/Vite client. Docker services and
the optional deployment configuration remain planned. The
[annotated project tree](docs/project-structure.md) shows file ownership.

## Contributing

This project is most useful when its contracts and implementation maturity
stay clear. Pick a focused slice, add tests with the behavior, keep external
services behind adapters, and update the matching guide when a contract
changes. Start with the [development guide](docs/development.md).

Never commit credentials, private videos, model weights, or downloaded
datasets. Review [security limitations](docs/security.md) before exposing
any service to untrusted users or networks.

## License

Vidsearch is distributed under the [MIT License](LICENSE).
