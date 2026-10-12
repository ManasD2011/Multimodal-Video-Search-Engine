# API

## Local development API

Run the service from the repository root after installing `.[api,search,visual]`:

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
| `GET` | `/healthz` | API readiness | `{"status":"ok","search_ready":true}` when local search is configured |
| `POST` | `/ingest/upload` | Upload a local video | Multipart `file`; returns a record while visual and speech indexing runs in the background |
| `POST` | `/ingest/url` | Import a video from YouTube | JSON `{"url":"https://www.youtube.com/watch?v=..."}`; downloads a permitted video then indexes visual frames and speech |
| `GET` | `/videos` | List local library | Array of video records |
| `GET` | `/videos/{video_id}` | Read one record | Video record or `404` |
| `GET` | `/videos/{video_id}/media` | Stream original file | Media response or `404` |
| `DELETE` | `/videos/{video_id}` | Delete file and record | `204` or `404` |
| `POST` | `/search` | Search indexed video evidence | JSON `{ "query": "...", "top_k": 20, "filters": {} }`; returns timestamped visual-frame and transcript matches |

Allowed upload filename extensions are `.mp4`, `.mkv`, `.mov`, `.webm`, and
`.avi`. `VIDSEARCH_MAX_VIDEO_BYTES` bounds the upload and defaults to 2 GB.
The API transcribes speech locally with Faster-Whisper's CPU `base` model and
samples frames at `VIDSEARCH_FRAME_RATE` (default one frame per second). A
local `clip-ViT-B-32` image-text model embeds each frame and search query.
Transcript chunks and frame embeddings are persisted in SQLite and loaded at
startup; old transcript-only videos are automatically queued for visual
indexing. Library records report `indexing`, `ready`, or `failed`;
`processing_error` contains an actionable error when indexing fails. OCR and
audio-event evidence are not indexed.

URL import is restricted to public HTTPS URLs on YouTube domains. It rejects
credentials, nonstandard ports, private or non-YouTube destinations, playlists,
and videos beyond the configured byte and duration limits. Import only videos
you own or are authorized to use. The local API remains unauthenticated and
must not be exposed to an untrusted network.

The Vite dev server proxies API requests to `127.0.0.1:8000`. For another
deployment, set the frontend `VITE_API_BASE_URL` to the API origin. The API
allows local Vite origins by default; override with comma-separated
`VIDSEARCH_CORS_ORIGINS` values as appropriate.
