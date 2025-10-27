[![Build and Publish Docker Image](https://github.com/ilude/onboard/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ilude/onboard/actions/workflows/docker-publish.yml)

Run:
```
docker run -p 9830:9830 --rm ghcr.io/traefikturkey/onboard:latest

Access http://localhost:9830
```

## Personalization quick start

The personalization pipeline (ingestion, embeddings, topic interests, and recommendations) is bundled with simple Make targets.

- Ingest bookmarks/layout and generate embeddings:
	- `make ingest`

- Summarize what was ingested and preview recommendations:
	- `make discover`

- Import existing app click events (optional) and backfill topics to improve recommendations:
	- `make sync-clicks`
	- `make topics-backfill`
	- `make ctr-update` (optional) to refresh per-source CTR priors

- Bootstrap topics even with few/no clicks (optional):
	- `make topics-seed-bookmarks` — seed topics based on bookmark titles
	- `make topics-from-titles` — add small prior weights from all item titles
	- `make prune-topics` — remove stopwords and overly-generic terms from topics

Advanced tuning (environment variables):

- Title seeding selector (TF–IDF-based):
	- `TOPIC_TOP_K_PER_TITLE` (default 5)
	- `TOPIC_MIN_DF` (default 2)
	- `TOPIC_MAX_DF_RATIO` (default 0.5)
	- `TOPIC_USE_BIGRAMS` (1 to enable, 0 to disable; default 1)

- Pruning:
	- `TOPIC_PRUNE_MAX_DF_RATIO` (default 0.6)
	- `TOPIC_PRUNE_DRY_RUN` (0/1; default 0)

### Vector store configuration (CHROMA_URL)

Embeddings are stored in Chroma. Configure it with a single environment variable `CHROMA_URL`:

- If `CHROMA_URL` starts with `http://` or `https://`, it's treated as a remote Chroma server URL.
- Otherwise, it's treated as a filesystem path for on-disk persistence (no server required).
- If unset, a local path under `app/configs/` is used by default.

Examples:
- Local on-disk persistence (default): no config needed; data will be written under `app/configs/`.
- Remote server: set `CHROMA_URL=http://localhost:8000` (or your server URL) before running the Make targets.

Notes:
- The ingestion and embedding refresher are idempotent. Re-running will only process new or missing items.
- Recommendations will improve once click events are present (either by using the app or via the optional sync/backfill steps above).
