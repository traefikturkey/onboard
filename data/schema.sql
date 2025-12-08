-- Onboard Personalization Schema (per PRD)
-- Click events
CREATE TABLE IF NOT EXISTS click_events (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'default',
  source_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  clicked_at INTEGER NOT NULL
);

-- Canonical items
CREATE TABLE IF NOT EXISTS items (
  item_id TEXT PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  title TEXT,
  source TEXT,
  published_at INTEGER,
  content_hash TEXT,
  vec_id TEXT,
  last_embedded_at INTEGER
);

-- Interest topics histogram
CREATE TABLE IF NOT EXISTS topics (
  token TEXT PRIMARY KEY,
  wt_long REAL NOT NULL DEFAULT 0.0,
  wt_short REAL NOT NULL DEFAULT 0.0,
  last_updated INTEGER
);

-- Parameters and weights (runtime configurable)
CREATE TABLE IF NOT EXISTS model_params (
  key TEXT PRIMARY KEY,
  val TEXT
);

-- Recommendation logs
CREATE TABLE IF NOT EXISTS rec_logs (
  rec_id TEXT,
  item_id TEXT,
  score REAL,
  served_at INTEGER,
  clicked INTEGER DEFAULT 0,
  PRIMARY KEY (rec_id, item_id)
);
