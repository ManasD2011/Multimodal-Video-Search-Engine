# Configuration reference

`Settings` in `src/vidsearch/core/config.py` reads the variables listed below
through `Settings.from_env()`. Values are defaults and input limits, not a
complete application configuration system. The app factory does not yet wire
settings into all route, worker, model, or storage providers.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VIDSEARCH_DATA_DIR` | `data` | Intended local media/data root |
| `VIDSEARCH_MAX_VIDEO_BYTES` | `2000000000` | Maximum media size accepted by callers using the setting |
| `VIDSEARCH_MAX_VIDEO_DURATION_SECONDS` | `3600` | Maximum probed media duration |
| `VIDSEARCH_FRAME_RATE` | `1` | Intended video frame sampling rate |
| `VIDSEARCH_SEGMENT_SECONDS` | `10` | Fixed-window segment duration |
| `VIDSEARCH_RETRIEVAL_TOP_K` | `20` | Default retrieval result limit |
| `VIDSEARCH_QDRANT_URL` | `http://localhost:6333` | Qdrant URL setting; store client is not configured |
| `VIDSEARCH_DATABASE_URL` | `sqlite:///data/vidsearch.db` | Database URL setting; SQL models/session are not configured |

Settings are converted from environment strings to `Path`, integer, or
floating-point values. Invalid numeric values raise an error; invalid
positive limits are rejected by the `Settings` dataclass.

## `.env.example` notes

`.env.example` is a copyable reference, not an automatically loaded file.
There is no `python-dotenv` dependency or `.env` loading call in the current
application. Export variables in the process environment or use a secure
environment manager. Do not commit `.env` or place credentials in the
example file.

The example also lists `REDIS_URL`, `VIDSEARCH_DEVICE`, and
`VIDSEARCH_MODEL_CACHE_DIR`. These are not currently read by `Settings.from_env`
or wired to an active integration; they reserve names for future queue and
model configuration.

## Configuration still needed

Before using external services, define and validate configuration for model
identifiers and revisions, inference device and precision, Qdrant collection
and vector dimensions, database migrations, Redis queue names, worker
concurrency, API authentication, CORS, logging, rate limits, retention, and
per-user quotas. Keep secrets out of YAML examples and source control.

The original proposal included `configs/default.yaml`, `configs/cpu.yaml`, and
`configs/eval.yaml`; those files do not exist yet. Current evaluation
configuration is passed to `eval.run_eval` with JSON (or YAML if PyYAML is
installed), and is separate from runtime `Settings`.
