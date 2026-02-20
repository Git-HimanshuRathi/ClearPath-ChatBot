"""
Query retrieval from FAISS index.
- Top-5 nearest neighbor search
- Similarity threshold filter (0.25)
- LRU cache for query embeddings
"""
import hashlib
from collections import OrderedDict
from typing import Optional

import faiss
import numpy as np

from rag.embed import embed_query

# Improvement 8: LRU cache for query embeddings
_CACHE_MAX_SIZE = 128
_query_cache: OrderedDict[str, np.ndarray] = OrderedDict()

# Improvement 3: Similarity threshold
SIMILARITY_THRESHOLD = 0.25
TOP_K = 5


def _cache_key(query: str) -> str:
    """Generate a cache key for the query string."""
    return hashlib.md5(query.strip().lower().encode()).hexdigest()


def _get_cached_embedding(query: str) -> Optional[np.ndarray]:
    """Retrieve cached embedding if available (LRU behavior)."""
    key = _cache_key(query)
    if key in _query_cache:
        _query_cache.move_to_end(key)
        return _query_cache[key]
    return None


def _cache_embedding(query: str, embedding: np.ndarray):
    """Store embedding in LRU cache, evicting oldest if full."""
    key = _cache_key(query)
    _query_cache[key] = embedding
    _query_cache.move_to_end(key)
    if len(_query_cache) > _CACHE_MAX_SIZE:
        _query_cache.popitem(last=False)


def retrieve(query: str, index: faiss.Index, chunks: list[dict]) -> list[dict]:
    """
    Embed query and retrieve top-K relevant chunks from the FAISS index.
    
    Improvement 3: Filters chunks below similarity threshold (0.25).
    Improvement 7: Returns document_name, chunk_id, and similarity_score per chunk.
    Improvement 8: Uses LRU cache for query embeddings.
    
    Args:
        query: User query string.
        index: FAISS index.
        chunks: List of chunk metadata dicts.
    
    Returns:
        List of dicts with keys: chunk_id, document_name, text, similarity_score
    """
    # Check cache first
    cached = _get_cached_embedding(query)
    cache_hit = cached is not None
    
    if cached is not None:
        query_embedding = cached
    else:
        query_embedding = embed_query(query)
        _cache_embedding(query, query_embedding)
    
    # Search FAISS index
    scores, indices = index.search(query_embedding, TOP_K)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        
        # Improvement 3: Apply similarity threshold
        if score < SIMILARITY_THRESHOLD:
            continue
        
        chunk = chunks[idx]
        results.append({
            "chunk_id": chunk["chunk_id"],
            "document_name": chunk["document_name"],
            "text": chunk["text"],
            "similarity_score": round(float(score), 4)
        })
    
    if cache_hit:
        print(f"  ⚡ Cache hit for query embedding")
    
    print(f"  Retrieved {len(results)} chunks above threshold "
          f"({SIMILARITY_THRESHOLD}) from {TOP_K} candidates")
    
    return results
