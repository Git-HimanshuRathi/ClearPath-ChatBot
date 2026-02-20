"""
Token-based text chunking using the all-MiniLM-L6-v2 tokenizer.
Chunks text into 500-token windows with 100-token overlap.
"""
from transformers import AutoTokenizer

# Load tokenizer once at module level
_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

CHUNK_SIZE = 500      # tokens per chunk
CHUNK_OVERLAP = 100   # token overlap between consecutive chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split documents into token-based chunks with overlap.
    
    Args:
        documents: List of dicts with keys: filename, text
    
    Returns:
        List of chunk dicts with keys: chunk_id, document_name, text
    """
    all_chunks = []
    chunk_id = 0
    
    for doc in documents:
        filename = doc["filename"]
        text = doc["text"]
        
        # Tokenize the entire document
        token_ids = _tokenizer.encode(text, add_special_tokens=False)
        
        # Create sliding window chunks
        start = 0
        while start < len(token_ids):
            end = min(start + CHUNK_SIZE, len(token_ids))
            chunk_tokens = token_ids[start:end]
            
            # Decode back to text
            chunk_text = _tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            
            all_chunks.append({
                "chunk_id": chunk_id,
                "document_name": filename,
                "text": chunk_text
            })
            chunk_id += 1
            
            # Move window forward
            if end >= len(token_ids):
                break
            start += CHUNK_SIZE - CHUNK_OVERLAP
    
    print(f"  Chunked {len(documents)} documents into {len(all_chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return all_chunks
