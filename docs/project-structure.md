# Project structure

This tree reflects the current workspace, including the FastAPI local-library
prototype, the React/Vite client, tests, and offline evaluation utilities.
Model-backed extraction and retrieval remain extension points rather than
implemented production services.

```text
.
├── .env.example                    Local settings template; no secrets
├── .gitignore                      Excludes local data and build artifacts
├── .pre-commit-config.yaml          Ruff and basic hygiene hooks
├── .github/
│   └── modernize/
│       └── assessment/
│           └── engines/
│               └── facts/
│                   └── architecture-diagram.md
├── LICENSE                         MIT license
├── Makefile                        Development command aliases
├── README.md                       Project overview and quick start
├── pyproject.toml                  Dependencies and Python tool configuration
├── src/
│   └── vidsearch/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py             Authentication and database hooks
│       │   ├── main.py             FastAPI application factory
│       │   ├── middleware.py       Middleware registration hook
│       │   ├── library.py          SQLite metadata and local media storage
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── ingest.py       Local video upload endpoint
│       │       ├── jobs.py         Job router placeholder
│       │       ├── search.py       Explicit not-configured search response
│       │       └── videos.py       Local video list, media, and delete routes
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py           Environment-backed settings
│       │   ├── logging.py          Logger naming helper
│       │   ├── schemas.py          Segment, Evidence, Query, hit contracts
│       │   └── security.py         Path, URL, and byte-size checks
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── audio_events.py     Audio-event extractor placeholder
│       │   ├── base.py             Extractor plugin contract
│       │   ├── caption.py          Caption extractor placeholder
│       │   ├── detection.py        Detection extractor placeholder
│       │   ├── ocr.py              OCR extractor placeholder
│       │   ├── registry.py         Explicit extractor registry
│       │   ├── speech.py           Speech extractor placeholder
│       │   └── visual.py           Visual extractor placeholder
│       ├── indexing/
│       │   ├── __init__.py
│       │   ├── bm25_store.py       In-memory lexical index
│       │   ├── metadata_db.py      Metadata persistence protocol
│       │   ├── pipeline.py         Extract-and-index orchestration
│       │   └── qdrant_store.py     Vector-store protocol and placeholder
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── audio.py            Audio extraction and VAD placeholders
│       │   ├── downloader.py       URL validation; download disabled
│       │   ├── frames.py           Frame sampler and motion-gate hooks
│       │   ├── loader.py           Local video file discovery
│       │   ├── probe.py            ffprobe metadata and media limits
│       │   └── segmenter.py        Fixed windows and scene hook
│       ├── query/
│       │   ├── __init__.py
│       │   ├── plan_schema.py      Validated query-plan contract
│       │   ├── planner.py          Model-backed planner placeholder
│       │   └── prompts.py          Planner prompt placeholder
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── fusion.py           Reciprocal-rank fusion
│       │   ├── lazy_index.py       Candidate enrichment placeholder
│       │   ├── rerank.py           Reranker placeholder
│       │   ├── search.py           Multi-retriever orchestration
│       │   └── temporal.py         Merge and selection helpers
│       └── workers/
│           ├── __init__.py
│           ├── queue.py            Queue protocol and factory hook
│           └── tasks.py            Ingest, reindex, delete placeholders
├── tests/
│   ├── README.md                   Test layout and implementation order
│   ├── conftest.py                 Shared pytest fixtures
│   ├── e2e/
│   │   └── search_flow.spec.ts     Playwright flow placeholder
│   ├── fixtures/
│   │   └── README.md               Synthetic fixture guidance
│   ├── integration/
│   │   ├── test_delete_cascade.py
│   │   ├── test_ingest_to_search.py
│   │   ├── test_jobs.py
│   │   └── test_video_api.py       Local library API integration tests
│   ├── load/
│   │   └── locustfile.py           Locust task placeholder
│   ├── security/
│   │   ├── test_authz.py
│   │   ├── test_prompt_injection.py
│   │   ├── test_ssrf.py
│   │   └── test_upload_attacks.py
│   └── unit/
│       ├── test_extractors.py
│       ├── test_fusion.py
│       ├── test_planner.py
│       ├── test_security.py
│       ├── test_segmenter.py
│       └── test_temporal.py
├── eval/
│   ├── README.md                   Evaluation formats and usage
│   ├── __init__.py
│   ├── ablations.py                Compare prediction exports
│   ├── benchmark_perf.py           Latency and index-size utility
│   ├── metrics.py                  Retrieval and temporal metrics
│   ├── run_eval.py                 JSONL evaluation command
│   ├── datasets/
│   │   ├── __init__.py
│   │   ├── msrvtt.py               MSR-VTT annotation normalizer
│   │   ├── qvhighlights.py         QVHighlights annotation normalizer
│   │   └── custom/
│   │       ├── README.md           Attribution and license notes
│   │       └── queries.jsonl       Synthetic example query
│   └── results/
│       └── .gitkeep                Empty results directory marker
├── frontend/
│   ├── e2e/
│   │   └── search-flow.spec.ts     Theme, search, upload, and delete flows
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts           Typed FastAPI client
│   │   │   └── client.test.ts      API client unit tests
│   │   ├── components/             Search, player, timeline, upload, and theme UI
│   │   ├── hooks/useTheme.ts       System, light, and dark theme preference
│   │   ├── pages/                  Search and dense table-style library pages
│   │   ├── styles/globals.css      Paper/vermilion design tokens and layout
│   │   ├── App.tsx                 Routes, shared state, and keyboard shortcuts
│   │   └── main.tsx                React/Vite entry point
│   ├── package.json                Frontend scripts and dependencies
│   ├── package-lock.json           Locked frontend dependency tree
│   ├── playwright.config.ts        Isolated API and Vite browser-test setup
│   └── vite.config.ts              Development server and API proxy
└── docs/
    ├── README.md                   Documentation index and maturity
    ├── api.md                      API routes and implementation status
    ├── architecture.md             System diagrams and module boundaries
    ├── assets/
    │   ├── README.md               Diagram asset maintenance guidance
    │   ├── application-architecture.svg
    │   └── component-relationships.svg
    ├── configuration.md            Environment settings and reserved values
    ├── development.md              Setup, checks, and contributor workflow
    ├── evaluation.md               Evaluation workflow and metric definitions
    ├── project-structure.md        This annotated file tree
    └── security.md                 Threat model and security gaps
```

## Package responsibilities

| Package | Owns |
| --- | --- |
| `core/` | Shared domain objects, settings, logging, and centralized validation |
| `ingestion/` | Safe local discovery, metadata probing, segmentation, and media hooks |
| `extractors/` | Evidence-stream interface, registry, and modality adapters |
| `indexing/` | Evidence indexing orchestration and storage boundaries |
| `query/` | Validated plan contract and future model planner |
| `retrieval/` | Backend orchestration, rank fusion, reranking, and temporal grouping |
| `api/` | HTTP app factory, route modules, dependencies, and middleware boundary |
| `workers/` | Queue boundary and background task entry points |
| `tests/` | Backend unit, integration, and security tests |
| `frontend/` | React/Vite interface and browser-level tests |
| `eval/` | Offline relevance and performance measurement |
| `docs/` | Architecture, interface, security, and developer guidance |

## Not in the current workspace

`configs/`, `docker/`, and `.github/workflows/` were in the original proposal
but are not present. The frontend is present, but model profiles, container
deployment, and CI workflows have not been added. The search API explicitly
supports timestamped spoken-word and local CLIP visual search. OCR and
audio-event evidence are not indexed yet.
