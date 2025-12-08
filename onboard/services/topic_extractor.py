from __future__ import annotations

import re
from typing import Dict, Iterable, List, Set, Tuple


_DEFAULT_STOPWORDS: Set[str] = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "how",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
    # Web noise / TLDs / boilerplate
    "www",
    "http",
    "https",
    "com",
    "net",
    "org",
    "io",
    "dev",
    "www",
    "amp",
    "html",
    "htm",
    "php",
    "json",
    "xml",
    "rss",
    "atom",
    "index",
    "home",
    "about",
    "contact",
}


_TOKEN_RX = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-\+]{2,}")


def extract_tokens(
    text: str, max_tokens: int = 100, stopwords: Iterable[str] | None = None
) -> List[str]:
    """Lightweight token extractor.

    - Falls back to regex tokenization; filters a small stopword list
    - Keeps alphanumerics, dashes/underscores/pluses
    - Lowercases tokens and de-duplicates while preserving order
    """
    if not text:
        return []
    sw = set(stopwords or _DEFAULT_STOPWORDS)
    toks = []
    seen: set[str] = set()
    for m in _TOKEN_RX.finditer(text):
        t = m.group(0).lower()
        # Basic normalization and filtering
        if t in sw:
            continue
        if t.isdigit():
            continue
        if len(t) < 3:
            continue
        # Drop tokens that are mostly punctuation-esque after stripping
        t_clean = t.strip("_-+")
        if not t_clean or t_clean in sw:
            continue
        if t in sw:
            continue
        if t in seen:
            continue
        seen.add(t)
        toks.append(t)
        if len(toks) >= max_tokens:
            break
    return toks


def _bigrams(tokens: List[str]) -> List[str]:
    out: List[str] = []
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if a in _DEFAULT_STOPWORDS or b in _DEFAULT_STOPWORDS:
            continue
        if a == b:
            continue
        # Simple bigram join; favors short, meaningful collocations
        out.append(f"{a} {b}")
    return out


def corpus_select_terms(
    texts: List[str],
    *,
    top_k_per_doc: int = 5,
    min_df: int = 2,
    max_df_ratio: float = 0.5,
    use_bigrams: bool = True,
    stopwords: Iterable[str] | None = None,
) -> List[List[str]]:
    """Select salient terms per document using a lightweight TF–IDF heuristic.

    - Tokenizes each text with extract_tokens and optional bigrams
    - Filters terms whose document frequency is too low/high
    - Scores terms by tf * idf where idf = log(1 + N/(1+df)) + 1
    - Returns top_k_per_doc terms per document
    """
    if not texts:
        return []

    sw = set(stopwords or _DEFAULT_STOPWORDS)
    N = len(texts)
    eff_min_df = 1 if N < min_df else min_df

    # Tokenize and build per-doc term sets/counters
    doc_terms: List[List[str]] = []
    doc_term_sets: List[Set[str]] = []
    for t in texts:
        tokens = extract_tokens(t or "", max_tokens=200, stopwords=sw)
        if use_bigrams:
            tokens = tokens + _bigrams(tokens)
        doc_terms.append(tokens)
        doc_term_sets.append(set(tokens))

    # Document frequency
    df: Dict[str, int] = {}
    for s in doc_term_sets:
        for term in s:
            df[term] = df.get(term, 0) + 1

    # Precompute IDF
    import math

    idf: Dict[str, float] = {}
    for term, d in df.items():
        # Filter by df bounds first
        if d < eff_min_df:
            continue
        if d / N > max_df_ratio:
            continue
        idf[term] = math.log(1.0 + (N / (1.0 + d))) + 1.0

    # Rank top terms per doc
    selected: List[List[str]] = []
    for terms in doc_terms:
        if not terms:
            selected.append([])
            continue
        # tf counts
        tf: Dict[str, int] = {}
        for term in terms:
            if term not in idf:
                continue
            tf[term] = tf.get(term, 0) + 1
        # score
        scored: List[Tuple[str, float]] = [
            (term, tf_val * idf[term]) for term, tf_val in tf.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        selected.append([t for t, _ in scored[:top_k_per_doc]])
    return selected
