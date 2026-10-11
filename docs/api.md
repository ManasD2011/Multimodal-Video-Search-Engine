# API

## Local development API

Run the service from the repository root after installing `.[api]`:

```powershell
python -m uvicorn --factory vidsearch.api.main:create_app --app-dir src --reload
```

The API currently uses SQLite metadata at `<VIDSEARCH_DATA_DIR>/vidsearch.sqlite3`
and saves media files below `<VIDSEARCH_DATA_DIR>/videos/`. The default data
root is `data/`. This is a single-user local development API, not a production
deployment: it has no authentication or per-user authorization and should not
be exposed to an untrusted network.

## Implemented endpoints

| Method | Path | Purpose | Contract |
|---|---|---|---|
| `GET` | `/healthz` | API readiness | `{"status":"ok","search_ready":false}` until retrieval is configured |
| `POST` | `/ingest/upload` | Upload a local video | Multipart `file`; returns library record with `status: "uploaded"` |
| `GET` | `/videos` | List local library | Array of video records |
| `GET` | `/videos/{video_id}` | Read one record | Video record or `404` |
| `GET` | `/videos/{video_id}/media` | Stream original file | Media response or `404` |
| `DELETE` | `/videos/{video_id}` | Delete file and record | `204` or `404` |
| `POST` | `/search` | Search indexed evidence | JSON `{ "query": "...", "top_k": 20, "filters": {} }`; returns `503` until a retrieval engine is wired |

Allowed upload filename extensions are `.mp4`, `.mkv`, `.mov`, `.webm`, and
`.avi`. `VIDSEARCH_MAX_VIDEO_BYTES` bounds the upload and defaults to 2 GB.
The API does not currently probe duration, inspect file signatures, create
segments, run extractors, or enqueue background jobs. Consequently duration
and segment counts are unknown/zero and upload status means only that bytes
were accepted and stored.

The Vite dev server proxies API requests to `127.0.0.1:8000`. For another
deployment, set the frontend `VITE_API_BASE_URL` to the API origin. The API
allows local Vite origins by default; override with comma-separated
`VIDSEARCH_CORS_ORIGINS` values as appropriate.
