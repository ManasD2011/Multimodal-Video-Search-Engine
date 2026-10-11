# Security

## Scope and trust boundaries

Video search processes untrusted user queries, local media, optional remote
URLs, extracted speech/OCR/captions, model outputs, and persistent search
records. Those values may be malformed or adversarial. Search results and
errors must be scoped to the authenticated user once multi-user access is
implemented.

This document describes the current scaffold and a checklist for completing
the security controls. It is not a production security assessment.

## Current controls and limitations

- `vidsearch.core.security.validate_local_path` resolves a path and checks
  that it remains beneath an existing allowed root.
- `validate_public_url` restricts URL schemes, rejects embedded credentials,
  and rejects hostnames that resolve to non-public IP addresses.
- `validate_file_size` provides a reusable byte-limit check.
- `probe_video` checks file size before invoking ffprobe and enforces a
  duration limit on returned metadata.
- The downloader and model-extraction functions are not wired to network or
  inference operations yet. URL validation by itself is not a safe download
  implementation.
- The local development API accepts bounded uploads, generates storage names,
  stores them under its data root, and rejects unsupported filename extensions.
  It does not inspect file signatures or decoded media properties.
- API authentication, per-user authorization, request rate limits, and worker
  controls are not implemented. Do not expose this API to untrusted users or
  networks.

## Threats and mitigations

| Threat | Required mitigation |
|---|---|
| Path traversal or symlink escape | Resolve user paths against a configured media root; keep the root private; avoid time-of-check/time-of-use races by opening validated files safely |
| Server-side request forgery | Allow only required HTTP(S) sources; reject private, loopback, link-local, and reserved ranges; re-check every redirect; pin validated DNS results to the actual connection to prevent DNS rebinding |
| Malicious or oversized media | Enforce upload and duration limits before expensive work; inspect actual file content rather than trusting MIME or extension; isolate FFmpeg/decoders with resource and time limits |
| Denial of service | Bound request bodies, concurrent jobs, frame count, decoded dimensions, query length, inference time, and search result count; apply per-user rate and queue limits |
| Cross-user data access | Authenticate every request and enforce ownership filters in metadata, vector search, job status, and deletion paths |
| Prompt injection in video-derived text | Treat transcript, OCR, captions, and indexed content strictly as data; never grant it authority over system instructions or tool execution |
| Sensitive data disclosure | Avoid logging raw media, transcripts, credentials, or full prompts; restrict result fields and storage access; define retention and deletion behavior |
| Dependency or model supply-chain risk | Pin and review dependencies and model revisions; scan dependencies and images; retrieve models from trusted sources and verify artifacts |

## Production-readiness checklist

- [ ] Implement authentication and object-level authorization for videos,
  segments, and jobs.
- [ ] Add upload validation for file signature, duration, dimensions, and
  decode resource use in addition to the local prototype's byte-count cap.
- [ ] Implement remote downloads in an isolated adapter with redirect checks,
  DNS/IP pinning, timeouts, byte limits, and an explicit host policy.
- [ ] Add request and inference rate limits, bounded queues, and cancellation.
- [ ] Keep media, model weights, indexes, and credentials outside source
  control; restrict service network exposure.
- [ ] Validate model and extractor output before indexing or returning it.
- [ ] Define safe logging, retention, deletion cascade, and backup policies.
- [ ] Run the upload-attack, SSRF, authorization, and prompt-injection tests
  against the completed implementation.
- [ ] Add security scans to CI and resolve findings before release.

## Reporting

Do not put secrets, private video, or personal data in issue reports. Include
the affected component, reproducible non-sensitive steps, and impact. Follow
the project's configured private vulnerability disclosure process when one is
established.
