"""
Embedding generation and FAISS index management.
- Uses sentence-transformers all-MiniLM-L6-v2
- Persists FAISS index and chunk metadata to disk
- Explicit L2 normalization for true cosine similarity (IndexFlatIP)
"""
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Default paths for persistence
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.bin")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")

# Global model reference (lazy-loaded)
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        print("  Loading embedding model: all-MiniLM-L6-v2 ...")
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("  ✓ Embedding model loaded")
    return _model


def build_index(chunks: list[dict]) -> tuple[faiss.Index, list[dict]]:
    """
    Generate embeddings for all chunks and build a FAISS IndexFlatIP.
    
    Improvement 1: Persists index + metadata to disk.
    Improvement 2: Explicit L2 normalization for cosine similarity.
    
    Args:
        chunks: List of chunk dicts with keys: chunk_id, document_name, text
    
    Returns:
        Tuple of (FAISS index, chunk metadata list)
    """
    model = get_model()
    
    texts = [c["text"] for c in chunks]
    print(f"  Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)
    
    # Improvement 2: Explicit L2 normalization for true cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Build IndexFlatIP (inner product = cosine similarity on normalized vectors)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    print(f"  ✓ FAISS index built: {index.ntotal} vectors, dim={dimension}")
    
    # Improvement 1: Persist to disk
    save_index(index, chunks)
    
    return index, chunks


def save_index(index: faiss.Index, chunks: list[dict]):
    """Save FAISS index and chunk metadata to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"  ✓ Index persisted to {INDEX_PATH}")


def load_index() -> tuple[faiss.Index, list[dict]] | None:
    """
    Load persisted FAISS index and chunk metadata from disk.
    Returns None if files don't exist.
    """
    if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(CHUNKS_PATH, "r") as f:
            chunks = json.load(f)
        print(f"  ✓ Loaded persisted index: {index.ntotal} vectors")
        return index, chunks
    return None


def embed_query(query: str) -> np.ndarray:
    """
    Generate and normalize embedding for a single query string.
    
    Returns:
        Normalized 1×D float32 numpy array.
    """
    model = get_model()
    embedding = model.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(embedding)
    return embedding
