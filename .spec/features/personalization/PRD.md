# Onboard – Personalization & Interest Map (PRD)

**Decision Locks:**

* **Primary storage:** SQLite (metadata) **+ ChromaDB** (vector search)
* **Text to embed:** **Title + Readability-extracted main text** (T2)

---

## 1) Overview & Goals

Turn Onboard into a personalized reader that blends **long‑term tastes** with **short‑term focus**. Use curated bookmarks as priors, clicks as signals, and embed article content to rank what to read next. Support proactive query generation for topics you care about but haven’t seen recently.

### Success Criteria

* CTR@10 improves over baseline feed ordering by ≥15% after 2 weeks.
* Latency for `/api/recommendations` p95 ≤ 300ms for 200 candidates (warm model).
* Cold start produces sensible recs using only bookmarks.

---

## 2) Architecture (B+T2)

```
RSS/Feeds ─┐                          ┌─> ChromaDB (vectors)
Bookmarks  ├─> TextExtractor (readability) ─┤
           └─> EmbeddingService (MiniLM) ───┤
Click Logs ────────────────────────────────┐ └─> SQLite (metadata, events, topics)
                                           │
                            InterestMapService (long/short centroids, topics)
                                           │
                                  RankingEngine (scoring)
                                           │
                              /api/recommendations (JSON)
```

* **TextExtractor**: fetches page; runs Readability; cleans text (strip boilerplate, normalize whitespace).
* **EmbeddingService**: SentenceTransformers `all-MiniLM-L6-v2` (384-dim), batch size 32, FP32 CPU ok.
* **VectorStore**: ChromaDB (Docker) with a single collection; metadata includes `url`, `title`, `source`, `published_at`, `hash`.
* **SQLite**: authoritative for events, item metadata, topic histograms, model params.

---

## 3) Data Model

### 3.1 SQLite Tables (DDL)

```sql
-- Clicks (existing or migrate to this)
CREATE TABLE IF NOT EXISTS click_events (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'default',
  source_id TEXT NOT NULL,           -- widget/feed/bookmark id
  item_id TEXT NOT NULL,             -- stable id for url
  url TEXT NOT NULL,
  title TEXT,
  clicked_at INTEGER NOT NULL        -- epoch seconds
);

-- Canonical items known to the system
CREATE TABLE IF NOT EXISTS items (
  item_id TEXT PRIMARY KEY,          -- stable hash of url
  url TEXT NOT NULL UNIQUE,
  title TEXT,
  source TEXT,                       -- feed name or 'bookmark'
  published_at INTEGER,              -- epoch seconds (feed pubdate)
  content_hash TEXT,                 -- sha256 of extracted text
  vec_id TEXT,                       -- id in ChromaDB
  last_embedded_at INTEGER
);

-- Interest topics histogram (aggregated keywords/entities)
CREATE TABLE IF NOT EXISTS topics (
  token TEXT PRIMARY KEY,
  wt_long REAL NOT NULL DEFAULT 0.0,
  wt_short REAL NOT NULL DEFAULT 0.0,
  last_updated INTEGER
);

-- Parameters and weights (runtime-configurable)
CREATE TABLE IF NOT EXISTS model_params (
  key TEXT PRIMARY KEY,
  val TEXT
);

-- Recommendation logs (for eval)
CREATE TABLE IF NOT EXISTS rec_logs (
  rec_id TEXT,
  item_id TEXT,
  score REAL,
  served_at INTEGER,
  clicked INTEGER DEFAULT 0,
  PRIMARY KEY (rec_id, item_id)
);
```

### 3.2 ChromaDB

* **Collection:** `onboard_items`
* **Embedding dim:** 384 (MiniLM)
* **Metadata keys:** `item_id`, `url`, `title`, `source`, `published_at`, `content_hash`

---

## 4) Text Extraction (T2)

* HTTP fetch with 8s timeout, `User-Agent: OnboardBot/1.0`.
* Run Readability (python-readability) to extract main content; fall back to `<title>` only if extraction fails.
* Normalize: lowercase (for topics), keep original case for embedding; remove scripts/styles; collapse whitespace.
* Truncate body to 2000 tokens equivalent (approx. 10k chars) before embedding to bound latency.

---

## 5) Embeddings

* Model: `sentence-transformers/all-MiniLM-L6-v2` (CPU OK).
* Inputs: `title + "\n\n" + readable_text[:N]`.
* Batch: 32 items; cache by `content_hash`.
* Store vectors in ChromaDB; store `vec_id` in SQLite `items`.

---

## 6) Interest Map

Two vector profiles plus a topic histogram.

### 6.1 Time Decay

For an interaction at time Δt (seconds) in the past:

```
weight(Δt; T_half) = exp(-ln(2) * Δt / T_half)
```

Default half-lives:

* **Short-term**: `T_half_short = 7 days`
* **Long-term**: `T_half_long  = 90 days`

### 6.2 Profile Updates

Let `v` be the embedding of an item; update running centroids incrementally:

```
α_short = base_click_wt * weight(Δt; T_half_short)
α_long  = base_click_wt * weight(Δt; T_half_long)

short_vec = normalize(short_vec * (1 - α_short) + v * α_short)
long_vec  = normalize(long_vec  * (1 - α_long)  + v * α_long)
```

* **Bookmarks prior:** For each bookmark URL, add once with `α_long = bookmark_wt` (no short update) to seed long‑term taste.
* Defaults: `base_click_wt=0.5`, `bookmark_wt=0.8` (configurable in `model_params`).

### 6.3 Topics Histogram

* Extract tokens/entities from title + readable text (spaCy).
* Increment `wt_short += β_short * weight(Δt; T_half_short)` and `wt_long += β_long * weight(Δt; T_half_long)`.
* Defaults: `β_short=1.0`, `β_long=0.3`.
* Periodically decay all rows by multiplying with `weight(Δt_since_last; T_half_*)`.

---

## 7) Candidate Generation

* From **feed cache**: N latest per feed (e.g., 50) within last 7 days.
* From **vector search**: query ChromaDB with `short_vec` for K similar historic items to find adjacent topics → fetch related fresh items from same sources (optional heuristic).
* Deduplicate by canonical URL; drop seen items (recent `click_events`).

---

## 8) Ranking

### 8.1 Score Components

```
S_long  = cosine(item_vec, long_vec)
S_short = cosine(item_vec, short_vec)
S_time  = weight(now - item_published_at; T_half_time)     -- freshness boost, T_half_time=3 days
S_src   = source_prior[item.source]                        -- learned CTR per source (default 0)
S_dup   = seen_penalty[item_id]                            -- 0 if unseen, -0.25 if shown recently
```

### 8.2 Final Score (defaults)

```
score = 0.40 * S_long
      + 0.45 * S_short
      + 0.10 * S_time
      + 0.07 * S_src
      + (-0.12) * I_shown_recently
```

* All weights configurable at runtime via `model_params`.
* Normalize cosine to [0,1] via `(c+1)/2` before combining.

### 8.3 Exploration

* ε‑greedy with ε=0.05: with 5% probability, inject a mid‑scored but novel topic candidate.

---

## 9) Proactive Query Generation

* Identify tokens where `wt_long` high but `wt_short` low.
* Templates: `"{token} tutorial"`, `"{token} best practices"`, `"{token} troubleshooting"`.
* (Optional) Call a search API; otherwise, just display suggested queries for manual use.

---

## 10) Services & Interfaces

### 10.1 TextExtractor

```python
class TextExtractor:
    def extract(self, url: str) -> Extracted:
        # fetch + readability + cleaning
```

### 10.2 EmbeddingService

```python
class EmbeddingService:
    def embed_texts(self, texts: list[str]) -> list[np.ndarray]
```

### 10.3 VectorStore (ChromaAdapter)

```python
class VectorStore:
    def upsert(self, item_id: str, vector: np.ndarray, metadata: dict) -> str
    def query(self, vector: np.ndarray, top_k: int) -> list[Result]
```

### 10.4 InterestMapService

```python
class InterestMapService:
    def update_from_click(self, item_id: str, ts: int): ...
    def seed_from_bookmark(self, item_id: str): ...
    def get_profiles(self) -> dict  # return long/short vectors + top topics
```

### 10.5 RankingEngine

```python
class RankingEngine:
    def score_items(self, item_ids: list[str]) -> list[ScoredItem]
```

---

## 11) API Contracts

### GET `/api/recommendations`

**Query:** `limit=20`
**Response:**

```json
{
  "generated_at": 1730000000,
  "items": [
    {
      "item_id": "sha1..",
      "url": "https://...",
      "title": "...",
      "score": 0.83,
      "source": "phoronix",
      "published_at": 1729900000
    }
  ]
}
```

### GET `/api/interest_map`

Returns centroid magnitudes, top tokens, and a debug view of params.

### POST `/api/feedback`

```json
{ "item_id": "...", "signal": "up" | "down" }
```

Applies a small immediate update: up → add to short_vec; down → apply negative feedback (push away) with small α.

---

## 12) Batch Jobs

* **EmbedRefresher**: (hourly) embed new items; update `items.vec_id`.
* **DecaySweep**: (daily) apply decay to topic rows.
* **CTRUpdater**: (daily) compute per‑source priors.
* **ModelEval**: (daily) compute CTR@k, nDCG@k; write to logs.

---

## 13) Training Loop (Optional Phase)

* Build pairwise data from sessionized clicks: clicked vs. skipped items.
* Features: `S_long`, `S_short`, `S_time`, `S_src`, token overlaps, position bias.
* Train XGBoost ranker; export feature weights to `model_params` or serve as a separate scorer.

---

## 14) Docker & Config

### 14.1 `docker-compose.yml` (snippet)

```yaml
services:
  chroma:
    image: chromadb/chroma:latest
    ports: ["8000:8000"]
    volumes:
      - ./data/chroma:/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
```

### 14.2 App Config (YAML)

```yaml
personalization:
  half_life:
    short_days: 7
    long_days: 90
  weights:
    long: 0.40
    short: 0.45
    recency: 0.10
    source: 0.07
    shown_penalty: -0.12
  bookmark_wt: 0.8
  base_click_wt: 0.5
  freshness_half_days: 3
```

---

## 15) Docling – Future Use

* **Supported:** HTML, PDF, DOCX, PPTX, images (with OCR).
* **Use Later When:** ingesting whitepapers/manuals, scanning PDFs, or normalizing complex docs into structured JSON/Markdown.
* **Integration Point:** behind `TextExtractor` interface; swap Readability path for Docling path per MIME type.
* **Non-goal (now):** fetching pages—Docling doesn’t fetch; we still handle HTTP.

---

## 16) Phased Delivery & Acceptance

### Phase 1 – Parsers & Storage (✅ exit)

* Bookmark + layout parsers produce a flat URL list with deduped `item_id`.
* Items table populated; embedding refresher upserts vectors.

### Phase 2 – Interest Map (✅ exit)

* Clicks update centroids and topics; `/api/interest_map` returns sensible data.

### Phase 3 – Ranking & API (✅ exit)

* `/api/recommendations` returns ranked items; p95 ≤ 300ms for 200 candidates.

### Phase 4 – UI & Feedback (✅ exit)

* “Recommended for You” widget + feedback controls; CTR@10 improves ≥15% vs baseline.

---

## 17) Testing

* Unit: extractor, embedder, vector adapter, decay math, scorer.
* Integration: end-to-end from feed → extract → embed → rank.
* Regression: snapshot scores for a fixed candidate set.

---

## 18) Risks & Mitigations

* **Fetcher latency**: cap timeouts; embed titles-only as fallback.
* **Embed cost**: cache by `content_hash`; batch embeds.
* **Cold start**: rely on bookmarks prior + source priors.
* **Drift**: regular decay sweeps; logs to audit.
