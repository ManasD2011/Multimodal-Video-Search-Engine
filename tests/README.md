# Test suite scaffold

This directory mirrors the test tiers for `vidsearch`. Some model, retrieval, worker, and persistence integrations are still
placeholders. The local API upload/library routes and their integration tests
are implemented, while the other test modules remain scaffolds. Replace each
`pytest.skip` placeholder as the matching behavior is implemented.

## Layout

- `unit/`: deterministic tests for segmentation, extractors, fusion, planning,
  temporal grouping, and security helpers.
- `integration/`: local upload/library/media/delete API coverage plus planned
  ingestion-to-search and job lifecycle tests.
- `security/`: upload validation, SSRF, authorization boundaries, and prompt
  injection handling.
- `load/`: Locust entry point for exercising the search API once its contract
  and test data setup are available.
- `e2e/`: Playwright search-flow entry point for the frontend.
- `fixtures/`: reusable generated media fixtures; do not commit real videos.

Keep generated media, model weights, and downloaded datasets out of version
control. Prefer synthetic, short fixtures and isolated test records.

## Suggested implementation order

1. Fill in `unit/` tests alongside `core/`, `ingestion/`, `extractors/`,
   `retrieval/`, and `query/`.
2. Add integration coverage when the API, worker, and backing services exist.
3. Implement the security cases alongside their corresponding API boundaries.
4. Wire Locust and Playwright into their own runners after their endpoint/UI
   contracts are available.

The integration, load, and browser tests should not depend on developer-owned
services or pre-existing data. Use temporary resources and clean them up.
