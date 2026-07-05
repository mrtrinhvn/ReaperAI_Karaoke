#!/usr/bin/env python3
"""
Hybrid Search Engine for ag-kit Knowledge Graph.

Adapted from Semble's search architecture:
  - BM25 keyword search (pure Python, no external deps)
  - TF-IDF semantic proxy (upgradeable to model2vec when available)
  - RRF (Reciprocal Rank Fusion) score combination
  - Code-aware tokenizer (camelCase, snake_case splitting)
  - Symbol-query vs NL-query auto-detection with adaptive alpha

Usage:
  python graph_search.py <graph.json> "search query"
  python graph_search.py <graph.json> "search query" --top 20
  python graph_search.py <graph.json> "search query" --mode semantic
  python graph_search.py <graph.json> "search query" --mode keyword
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ──────────────────────────────────────────────
# Rerank Penalties — from Semble's penalties.py
# Demote test files, compat dirs, examples, re-exports
# ──────────────────────────────────────────────
_TEST_FILE_RE = re.compile(
    r"(?:^|/)"
    r"(?:"
    r"test_[^/]*\.py|[^/]*_test\.py"
    r"|[^/]*_test\.go"
    r"|[^/]*Tests?\.java"
    r"|[^/]*\.test\.[jt]sx?"
    r"|[^/]*\.spec\.[jt]sx?"
    r"|[^/]*Tests?\.kt"
    r"|[^/]*Tests?\.swift"
    r"|[^/]*Tests?\.cs"
    r"|test_[^/]*\.cpp|[^/]*_test\.cpp"
    r"|[^/]*_test\.dart"
    r")$"
)
_TEST_DIR_RE = re.compile(r"(?:^|/)(?:tests?|__tests__|spec|testing)(?:/|$)")
_COMPAT_DIR_RE = re.compile(r"(?:^|/)(?:compat|_compat|legacy)(?:/|$)")
_EXAMPLES_DIR_RE = re.compile(r"(?:^|/)(?:_?examples?|docs?_src)(?:/|$)")
_TYPE_DEFS_RE = re.compile(r"\.d\.ts$")
_REEXPORT_FILENAMES = frozenset({"__init__.py", "package-info.java", "index.ts", "index.js"})

_STRONG_PENALTY = 0.3
_MODERATE_PENALTY = 0.5
_MILD_PENALTY = 0.7

# File saturation — max chunks from same file before decay
_FILE_SATURATION_THRESHOLD = 1
_FILE_SATURATION_DECAY = 0.5


def _file_path_penalty(file_path: str) -> float:
    """Combined multiplicative penalty for test/compat/example paths."""
    normalised = file_path.replace("\\", "/")
    penalty = 1.0
    if _TEST_FILE_RE.search(normalised) or _TEST_DIR_RE.search(normalised):
        penalty *= _STRONG_PENALTY
    name = Path(file_path).name
    if name in _REEXPORT_FILENAMES:
        penalty *= _MODERATE_PENALTY
    if _COMPAT_DIR_RE.search(normalised):
        penalty *= _STRONG_PENALTY
    if _EXAMPLES_DIR_RE.search(normalised):
        penalty *= _STRONG_PENALTY
    if _TYPE_DEFS_RE.search(normalised):
        penalty *= _MILD_PENALTY
    return penalty


def rerank_with_penalties(
    scored_indices: list[tuple[int, float]],
    nodes: list[dict[str, Any]],
    top_k: int,
) -> list[tuple[int, float]]:
    """Apply path penalties + file saturation decay, then return top-k.

    Adapted from Semble's rerank_topk() in penalties.py.
    """
    if not scored_indices:
        return []

    # Apply path penalties
    penalty_cache: dict[str, float] = {}
    penalised = []
    for idx, score in scored_indices:
        fp = nodes[idx].get("file_path", "")
        if fp and fp not in penalty_cache:
            penalty_cache[fp] = _file_path_penalty(fp)
        pen = penalty_cache.get(fp, 1.0)
        penalised.append((idx, score * pen))

    # Sort by penalised score descending
    penalised.sort(key=lambda x: -x[1])

    # File saturation decay — greedy selection
    file_selected: dict[str, int] = {}
    selected: list[tuple[int, float]] = []

    for idx, pen_score in penalised:
        if len(selected) >= top_k * 2:  # over-select then trim
            break
        fp = nodes[idx].get("file_path", "")
        already = file_selected.get(fp, 0)
        eff_score = pen_score
        if already >= _FILE_SATURATION_THRESHOLD:
            excess = already - _FILE_SATURATION_THRESHOLD + 1
            eff_score *= _FILE_SATURATION_DECAY ** excess
        selected.append((idx, eff_score))
        file_selected[fp] = already + 1

    selected.sort(key=lambda x: -x[1])
    return selected[:top_k]

# ──────────────────────────────────────────────
# Code-aware Tokenizer — from Semble's tokens.py
# ──────────────────────────────────────────────
_TOKEN_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")

# Symbol query detector — from Semble's boosting.py
_SYMBOL_QUERY_RE = re.compile(
    r"^(?:"
    r"[A-Za-z_][A-Za-z0-9_]*(?:(?:::|\\|->|\.)[A-Za-z_][A-Za-z0-9_]*)+"  # namespace-qualified
    r"|_[A-Za-z0-9_]*"  # leading underscore
    r"|[A-Za-z][A-Za-z0-9]*[A-Z_][A-Za-z0-9_]*"  # contains uppercase or underscore
    r"|[A-Z][A-Za-z0-9]*"  # starts with uppercase
    r")$"
)

_STOPWORDS = frozenset(
    "a an and are as at be by do does for from has have how if in is it not of on or the to was"
    " what when where which who why with".split()
)


def split_identifier(token: str) -> list[str]:
    """Split a single identifier into sub-tokens via camelCase/snake_case."""
    lower = token.lower()
    parts: list[str] = []
    if "_" in token:
        parts = [p for p in lower.split("_") if p]
    else:
        parts = [m.lower() for m in _CAMEL_RE.findall(token)]
    if len(parts) >= 2:
        return [lower, *parts]
    return [lower]


def tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens for BM25 indexing.

    Compound identifiers expanded into sub-tokens for partial matching.
    """
    raw_tokens = _TOKEN_RE.findall(text)
    result: list[str] = []
    for tok in raw_tokens:
        result.extend(split_identifier(tok))
    return result


def is_symbol_query(query: str) -> bool:
    """Return True if query looks like a code symbol."""
    return _SYMBOL_QUERY_RE.match(query.strip()) is not None


# ──────────────────────────────────────────────
# BM25 — Pure Python implementation
# Parameters from Robertson & Walker (1994)
# ──────────────────────────────────────────────
_BM25_K1 = 1.5
_BM25_B = 0.75


@dataclass
class BM25Index:
    """Pure Python BM25 index. No external dependencies."""

    doc_tokens: list[list[str]] = field(default_factory=list)
    doc_lens: list[int] = field(default_factory=list)
    avg_dl: float = 0.0
    n_docs: int = 0
    # term -> {doc_id: term_freq}
    inverted_index: dict[str, dict[int, int]] = field(default_factory=dict)
    # term -> doc_freq
    df: dict[str, int] = field(default_factory=dict)

    def build(self, documents: list[list[str]]) -> None:
        """Build the BM25 index from tokenized documents."""
        self.doc_tokens = documents
        self.n_docs = len(documents)
        self.doc_lens = [len(doc) for doc in documents]
        self.avg_dl = sum(self.doc_lens) / max(self.n_docs, 1)

        self.inverted_index = {}
        self.df = {}

        for doc_id, tokens in enumerate(documents):
            tf = Counter(tokens)
            for term, freq in tf.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                    self.df[term] = 0
                self.inverted_index[term][doc_id] = freq
                self.df[term] += 1

    def score(self, query_tokens: list[str]) -> list[float]:
        """Score all documents against query tokens. Returns list of scores."""
        scores = [0.0] * self.n_docs

        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            doc_freq = self.df[term]
            # IDF with smoothing
            idf = math.log((self.n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
            if idf <= 0:
                continue

            for doc_id, tf in self.inverted_index[term].items():
                dl = self.doc_lens[doc_id]
                # BM25 TF normalization
                numerator = tf * (_BM25_K1 + 1)
                denominator = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / self.avg_dl)
                scores[doc_id] += idf * (numerator / denominator)

        return scores


# ──────────────────────────────────────────────
# TF-IDF Cosine Similarity — semantic proxy
# Upgradeable to model2vec when available
# ──────────────────────────────────────────────
@dataclass
class TFIDFIndex:
    """Pure Python TF-IDF cosine similarity index."""

    vocab: dict[str, int] = field(default_factory=dict)
    idf: dict[str, float] = field(default_factory=dict)
    doc_vectors: list[dict[str, float]] = field(default_factory=list)
    n_docs: int = 0

    def build(self, documents: list[list[str]]) -> None:
        """Build the TF-IDF index from tokenized documents."""
        self.n_docs = len(documents)
        self.doc_vectors = []

        # Build vocabulary and document frequency
        df: dict[str, int] = {}
        for tokens in documents:
            seen = set()
            for token in tokens:
                if token not in seen:
                    df[token] = df.get(token, 0) + 1
                    seen.add(token)

        # IDF
        self.idf = {}
        for term, freq in df.items():
            self.idf[term] = math.log((self.n_docs + 1) / (freq + 1)) + 1.0

        # TF-IDF vectors (sparse)
        for tokens in documents:
            tf = Counter(tokens)
            vector: dict[str, float] = {}
            norm = 0.0
            for term, count in tf.items():
                if term in self.idf:
                    weight = (count / max(len(tokens), 1)) * self.idf[term]
                    vector[term] = weight
                    norm += weight * weight
            # Normalize
            if norm > 0:
                norm_factor = 1.0 / math.sqrt(norm)
                for term in vector:
                    vector[term] *= norm_factor
            self.doc_vectors.append(vector)

    def score(self, query_tokens: list[str]) -> list[float]:
        """Score all documents by cosine similarity with query."""
        # Build query vector
        tf = Counter(query_tokens)
        query_vector: dict[str, float] = {}
        norm = 0.0
        for term, count in tf.items():
            if term in self.idf:
                weight = (count / max(len(query_tokens), 1)) * self.idf[term]
                query_vector[term] = weight
                norm += weight * weight
        if norm > 0:
            norm_factor = 1.0 / math.sqrt(norm)
            for term in query_vector:
                query_vector[term] *= norm_factor

        # Cosine similarity
        scores = []
        for doc_vec in self.doc_vectors:
            dot = sum(query_vector.get(t, 0.0) * doc_vec.get(t, 0.0) for t in query_vector)
            scores.append(dot)
        return scores


# ──────────────────────────────────────────────
# RRF Fusion — from Semble's search.py
# ──────────────────────────────────────────────
_RRF_K = 60

# Alpha weighting — from Semble's weighting.py
_ALPHA_SYMBOL = 0.3  # lean BM25 for exact keyword matching
_ALPHA_NL = 0.5      # balanced semantic + BM25


def resolve_alpha(query: str, alpha: float | None = None) -> float:
    """Return blending weight for semantic scores. Auto-detect from query type."""
    if alpha is not None:
        return alpha
    return _ALPHA_SYMBOL if is_symbol_query(query) else _ALPHA_NL


def rrf_scores(raw_scores: dict[int, float]) -> dict[int, float]:
    """Convert raw scores to RRF scores: 1/(k + rank)."""
    if not raw_scores:
        return raw_scores
    ranked = sorted(raw_scores, key=lambda idx: -raw_scores[idx])
    return {idx: 1.0 / (_RRF_K + rank) for rank, idx in enumerate(ranked, 1)}


# ──────────────────────────────────────────────
# Search Result
# ──────────────────────────────────────────────
@dataclass
class SearchResult:
    node_id: str
    name: str
    node_type: str
    score: float
    file_path: str = ""
    summary: str = ""
    match_source: str = ""  # "hybrid", "semantic", "keyword"
    line_range: tuple[int, int] | None = None  # GAP 3: function-level precision


# ──────────────────────────────────────────────
# Graph Search Engine — the main class
# ──────────────────────────────────────────────
class GraphSearchEngine:
    """Hybrid search engine over a Knowledge Graph.

    Indexes nodes by their textual content (name, summary, tags, file_path).
    Supports BM25 keyword search, TF-IDF semantic proxy, and RRF fusion.
    """

    def __init__(self):
        self.nodes: list[dict[str, Any]] = []
        self.node_tokens: list[list[str]] = []
        self.bm25 = BM25Index()
        self.tfidf = TFIDFIndex()
        self._built = False

    def _node_to_text(self, node: dict[str, Any]) -> str:
        """Convert a node to searchable text.

        GAP 3 fix: function/class nodes get extra name repetition
        for higher boosting vs file-level nodes.
        """
        parts = []
        name = node.get("name", "")
        node_type = node.get("type", "")

        if name:
            parts.append(name)
            # Title field boosting — functions/classes get 3x name weight
            # (vs 2x for files) for function-level precision
            if node_type in ("function", "class"):
                parts.extend([name, name])  # 3x total
            else:
                parts.append(name)  # 2x total

        summary = node.get("summary", "")
        if summary:
            parts.append(summary)

        file_path = node.get("file_path", "")
        if file_path:
            p = Path(file_path)
            parts.append(p.stem)
            if p.parent.name and p.parent.name not in (".", "/"):
                parts.append(p.parent.name)

        tags = node.get("tags", [])
        if tags:
            parts.extend(tags)

        if node_type:
            parts.append(node_type)

        return " ".join(parts)

    def build_from_graph(self, graph_data: dict[str, Any]) -> None:
        """Build search indices from a loaded knowledge graph."""
        self.nodes = graph_data.get("nodes", [])
        if not self.nodes:
            return

        # Tokenize all nodes
        self.node_tokens = []
        for node in self.nodes:
            text = self._node_to_text(node)
            tokens = tokenize(text)
            self.node_tokens.append(tokens)

        # Build both indices
        self.bm25.build(self.node_tokens)
        self.tfidf.build(self.node_tokens)
        self._built = True

    def build_from_file(self, graph_path: str | Path) -> None:
        """Load a knowledge graph JSON and build indices."""
        data = json.loads(Path(graph_path).read_text(encoding="utf-8"))
        self.build_from_graph(data)

    def search(
        self,
        query: str,
        top_k: int = 10,
        mode: str = "hybrid",
        alpha: float | None = None,
    ) -> list[SearchResult]:
        """Search the knowledge graph.

        Args:
            query: Search query string.
            top_k: Number of results to return.
            mode: "hybrid" (default), "semantic", or "keyword".
            alpha: Weight for semantic score (0-1). None = auto-detect.

        Returns:
            List of SearchResult sorted by score descending.
        """
        if not self._built or not self.nodes:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        alpha_weight = resolve_alpha(query, alpha)
        candidate_count = top_k * 5

        if mode == "keyword":
            return self._search_bm25(query_tokens, top_k)
        elif mode == "semantic":
            return self._search_tfidf(query_tokens, top_k)
        else:
            return self._search_hybrid(query_tokens, top_k, alpha_weight, candidate_count)

    def _search_bm25(self, query_tokens: list[str], top_k: int) -> list[SearchResult]:
        """Pure BM25 keyword search."""
        scores = self.bm25.score(query_tokens)
        indexed_scores = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: -x[1])
        results = []
        for idx, score in indexed_scores[:top_k]:
            node = self.nodes[idx]
            results.append(SearchResult(
                node_id=node.get("id", ""),
                name=node.get("name", ""),
                node_type=node.get("type", ""),
                score=score,
                file_path=node.get("file_path", ""),
                summary=node.get("summary", ""),
                match_source="keyword",
                line_range=tuple(node["line_range"]) if node.get("line_range") else None,
            ))
        return results

    def _search_tfidf(self, query_tokens: list[str], top_k: int) -> list[SearchResult]:
        """TF-IDF cosine similarity search (semantic proxy)."""
        scores = self.tfidf.score(query_tokens)
        indexed_scores = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: -x[1])
        results = []
        for idx, score in indexed_scores[:top_k]:
            node = self.nodes[idx]
            results.append(SearchResult(
                node_id=node.get("id", ""),
                name=node.get("name", ""),
                node_type=node.get("type", ""),
                score=score,
                file_path=node.get("file_path", ""),
                summary=node.get("summary", ""),
                match_source="semantic",
                line_range=tuple(node["line_range"]) if node.get("line_range") else None,
            ))
        return results

    def _search_hybrid(
        self,
        query_tokens: list[str],
        top_k: int,
        alpha: float,
        candidate_count: int,
    ) -> list[SearchResult]:
        """Hybrid search with RRF fusion — from Semble's architecture."""
        # Get raw scores from both engines
        bm25_scores = self.bm25.score(query_tokens)
        tfidf_scores = self.tfidf.score(query_tokens)

        # Collect top candidates from each
        bm25_top: dict[int, float] = {}
        tfidf_top: dict[int, float] = {}

        bm25_indexed = [(i, s) for i, s in enumerate(bm25_scores) if s > 0]
        bm25_indexed.sort(key=lambda x: -x[1])
        for idx, score in bm25_indexed[:candidate_count]:
            bm25_top[idx] = score

        tfidf_indexed = [(i, s) for i, s in enumerate(tfidf_scores) if s > 0]
        tfidf_indexed.sort(key=lambda x: -x[1])
        for idx, score in tfidf_indexed[:candidate_count]:
            tfidf_top[idx] = score

        # RRF normalization
        rrf_bm25 = rrf_scores(bm25_top)
        rrf_tfidf = rrf_scores(tfidf_top)

        # Combine with alpha weighting
        all_candidates = set(rrf_bm25.keys()) | set(rrf_tfidf.keys())
        combined: dict[int, float] = {}
        for idx in all_candidates:
            semantic_score = rrf_tfidf.get(idx, 0.0)
            keyword_score = rrf_bm25.get(idx, 0.0)
            combined[idx] = alpha * semantic_score + (1.0 - alpha) * keyword_score

        # File coherence boost — from Semble's boost_multi_chunk_files
        if combined:
            file_scores: dict[str, float] = {}
            best_in_file: dict[str, int] = {}
            for idx, score in combined.items():
                fp = self.nodes[idx].get("file_path", "")
                if not fp:
                    continue
                file_scores[fp] = file_scores.get(fp, 0.0) + score
                if fp not in best_in_file or score > combined.get(best_in_file[fp], 0.0):
                    best_in_file[fp] = idx

            if file_scores:
                max_file = max(file_scores.values())
                max_combined = max(combined.values()) if combined else 1.0
                boost_unit = max_combined * 0.2
                for fp, best_idx in best_in_file.items():
                    combined[best_idx] += boost_unit * file_scores[fp] / max(max_file, 1e-9)

        # Apply rerank penalties (GAP 1+2 fix)
        sorted_results = sorted(combined.items(), key=lambda x: -x[1])
        reranked = rerank_with_penalties(
            [(idx, score) for idx, score in sorted_results],
            self.nodes,
            top_k,
        )

        results = []
        for idx, score in reranked:
            node = self.nodes[idx]
            results.append(SearchResult(
                node_id=node.get("id", ""),
                name=node.get("name", ""),
                node_type=node.get("type", ""),
                score=score,
                file_path=node.get("file_path", ""),
                summary=node.get("summary", ""),
                match_source="hybrid",
                line_range=tuple(node["line_range"]) if node.get("line_range") else None,
            ))
        return results

    def compute_savings(self, results: list[SearchResult]) -> dict[str, Any]:
        """Compute token savings: snippet chars vs full file chars.

        GAP 6 fix: Adapted from Semble's stats.py.
        """
        snippet_chars = sum(len(r.summary) for r in results)
        # Estimate full file sizes from node data
        seen_files: set[str] = set()
        file_chars = 0
        for r in results:
            if r.file_path and r.file_path not in seen_files:
                seen_files.add(r.file_path)
                # Find the file node to get line count
                for node in self.nodes:
                    if node.get("file_path") == r.file_path and node.get("type") == "file":
                        summary = node.get("summary", "")
                        # Parse line count from summary "filename.ts (typescript, 200 lines)"
                        import re as _re
                        m = _re.search(r'(\d+)\s+lines', summary)
                        if m:
                            file_chars += int(m.group(1)) * 40  # ~40 chars/line avg
                        break

        saved = max(0, file_chars - snippet_chars)
        pct = round(saved / max(file_chars, 1) * 100)
        return {
            "snippet_chars": snippet_chars,
            "file_chars": file_chars,
            "saved_chars": saved,
            "saved_pct": pct,
            "files_touched": len(seen_files),
        }


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Search a Knowledge Graph")
    parser.add_argument("graph_file", help="Path to knowledge-graph.json")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--mode", choices=["hybrid", "semantic", "keyword"], default="hybrid",
                        help="Search mode (default: hybrid)")
    parser.add_argument("--alpha", type=float, default=None,
                        help="Semantic weight 0-1 (default: auto-detect)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    engine = GraphSearchEngine()
    engine.build_from_file(args.graph_file)

    results = engine.search(args.query, top_k=args.top, mode=args.mode, alpha=args.alpha)

    if args.json:
        output = [{
            "id": r.node_id, "name": r.name, "type": r.node_type,
            "score": round(r.score, 6), "file": r.file_path,
            "summary": r.summary, "source": r.match_source,
            "line_range": list(r.line_range) if r.line_range else None,
        } for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        alpha_used = resolve_alpha(args.query, args.alpha)
        query_type = "symbol" if is_symbol_query(args.query) else "NL"
        print(f"🔍 Query: \"{args.query}\" [{query_type}] α={alpha_used:.2f} mode={args.mode}")
        print(f"   {len(results)} results from {len(engine.nodes)} nodes\n")

        for i, r in enumerate(results, 1):
            icon = {"file": "📄", "function": "⚙️", "class": "🏗️", "config": "⚙️",
                    "document": "📝", "service": "🐳", "table": "🗃️"}.get(r.node_type, "📦")
            line_info = f" L{r.line_range[0]}-{r.line_range[1]}" if r.line_range else ""
            print(f"  {i:2d}. {icon} {r.name}")
            print(f"      [{r.node_type}] score={r.score:.6f} ({r.match_source}){line_info}")
            if r.file_path:
                print(f"      📁 {r.file_path}")
            if r.summary and r.summary != r.name:
                print(f"      💬 {r.summary[:80]}")
            print()

        # GAP 6: Token savings stats
        savings = engine.compute_savings(results)
        if savings["file_chars"] > 0:
            bar_width = 16
            ratio = savings["saved_chars"] / max(savings["file_chars"], 1)
            filled = round(ratio * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            saved_k = savings["saved_chars"] // 4000  # ~4 chars/token
            print(f"   💰 Token Savings: [{bar}] ~{saved_k}k tokens saved ({savings['saved_pct']}%)")
            print(f"      Snippet: {savings['snippet_chars']} chars | Full files: {savings['file_chars']} chars")


if __name__ == "__main__":
    main()
