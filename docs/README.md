# Vidsearch documentation

This documentation describes the current repository, including incomplete
areas. It is intended to make the implementation boundaries explicit rather
than imply that every planned service or model is already available.

## Guides

| Document | Purpose |
| --- | --- |
| [Architecture](architecture.md) | System overview, data flow, diagrams, and current integration state |
| [Project structure](project-structure.md) | Annotated file tree and module ownership |
| [Configuration](configuration.md) | Supported environment settings and reserved variables |
| [API](api.md) | API factory, route status, and contract direction |
| [Security](security.md) | Threat boundaries, current controls, and work required before deployment |
| [Evaluation](evaluation.md) | Dataset formats, metrics, ablations, and performance measurements |
| [Development](development.md) | Environment setup, checks, and contribution conventions |

## Current maturity

The project is an implementation scaffold, not a production application.
Several modules provide useful pure-Python behavior or contracts, but their
external integrations remain unconfigured. In particular:

- FastAPI routers are mounted but contain no endpoint handlers.
- Extractor classes, frame/audio processing, query planning, and scene
  detection require implementations or provider adapters.
- The Qdrant class is an unconfigured adapter; metadata storage is a protocol.
- Queue creation, authentication, database sessions, and middleware are
  unconfigured.
- The tests mostly document intended cases and currently skip.
- The `frontend/`, `configs/`, `docker/`, and `.github/workflows/` directories
  shown in the original proposal are not present in this workspace.

See the [annotated tree](project-structure.md) and [architecture](architecture.md)
for file-by-file detail.

## Diagram sources

Architecture diagrams are maintained as Mermaid source in
[architecture.md](architecture.md), so they remain reviewable and versioned
alongside the written design. SVG previews are in [`assets/`](assets/).
