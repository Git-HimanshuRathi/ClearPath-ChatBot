"""
Clearpath RAG Chatbot — FastAPI Backend
POST /chat — Standard chat endpoint
POST /chat/stream — SSE streaming endpoint
"""
import os
import json
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from rag.ingest import ingest_pdfs
from rag.chunk import chunk_documents
from rag.embed import build_index, load_index, get_model
from rag.retrieve import retrieve
from router.router import classify_query
from evaluator.evaluator import evaluate_response
from llm.groq_client import chat_completion, chat_completion_stream
from logs.logger import log_request

# ─── Globals ────────────────────────────────────────────────────────────
faiss_index = None
chunk_metadata = None

# Conversation memory: session_id → list of last N user/assistant pairs
MAX_MEMORY = 3
conversation_memory: dict[str, list[dict]] = defaultdict(list)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")


# ─── Startup / Shutdown ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load or build FAISS index on startup."""
    global faiss_index, chunk_metadata
    
    print("\n🚀 Clearpath RAG Chatbot — Starting up...")
    
    # Try loading persisted index first
    loaded = load_index()
    if loaded:
        faiss_index, chunk_metadata = loaded
        print("  ✓ Using persisted FAISS index")
    else:
        print("  Building FAISS index from docs/ ...")
        documents = ingest_pdfs(DOCS_DIR)
        chunks = chunk_documents(documents)
        faiss_index, chunk_metadata = build_index(chunks)
        print("  ✓ FAISS index built and persisted")
    
    # Pre-load embedding model
    get_model()
    
    print(f"  ✓ Ready! Index contains {faiss_index.ntotal} vectors\n")
    yield
    print("\n👋 Shutting down Clearpath chatbot...")


# ─── App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Clearpath RAG Chatbot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ──────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")


class SourceInfo(BaseModel):
    chunk_id: int
    document_name: str
    similarity_score: float


class DebugInfo(BaseModel):
    classification: str
    model_used: str
    complex_score: int
    signals: list[str]
    tokens_input: int
    tokens_output: int
    latency_ms: float
    confidence: str
    flags: list[str]


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceInfo]
    debug: DebugInfo


# ─── Helper ─────────────────────────────────────────────────────────────
def _get_history(session_id: str) -> list[dict]:
    """Get conversation history for a session."""
    return list(conversation_memory[session_id])


def _update_history(session_id: str, query: str, response: str):
    """Store user/assistant pair in session memory (max N pairs)."""
    history = conversation_memory[session_id]
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": response})
    # Keep only last MAX_MEMORY pairs (2 messages each)
    if len(history) > MAX_MEMORY * 2:
        conversation_memory[session_id] = history[-(MAX_MEMORY * 2):]


# ─── Endpoints ──────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Pipeline: retrieve → route → call Groq → evaluate → log → respond
    """
    query = request.query.strip()
    session_id = request.session_id
    
    print(f"\n{'='*60}")
    print(f"  Query: {query}")
    print(f"  Session: {session_id}")
    
    # Step 1: Retrieve relevant chunks
    retrieved = retrieve(query, faiss_index, chunk_metadata)
    
    # Step 2: Route query to appropriate model
    routing = classify_query(query)
    
    # Step 3: Build context from retrieved chunks
    context = "\n\n".join(
        f"[Source: {c['document_name']}, Chunk #{c['chunk_id']}, "
        f"Similarity: {c['similarity_score']}]\n{c['text']}"
        for c in retrieved
    ) if retrieved else "No relevant documentation found."
    
    # Step 4: Call Groq LLM
    history = _get_history(session_id)
    llm_result = chat_completion(
        model=routing["model_used"],
        context=context,
        query=query,
        conversation_history=history,
    )
    
    # Step 5: Evaluate response
    evaluation = evaluate_response(llm_result["response"], retrieved)
    
    # Step 6: Log the request
    log_request(
        query=query,
        classification=routing["classification"],
        model_used=routing["model_used"],
        tokens_input=llm_result["tokens_input"],
        tokens_output=llm_result["tokens_output"],
        latency_ms=llm_result["latency_ms"],
        confidence=evaluation["confidence"],
        flags=evaluation["flags"],
        num_sources=len(retrieved),
    )
    
    # Step 7: Update conversation memory
    _update_history(session_id, query, evaluation["response"])
    
    # Step 8: Build response
    sources = [
        SourceInfo(
            chunk_id=c["chunk_id"],
            document_name=c["document_name"],
            similarity_score=c["similarity_score"],
        )
        for c in retrieved
    ]
    
    debug = DebugInfo(
        classification=routing["classification"],
        model_used=routing["model_used"],
        complex_score=routing["complex_score"],
        signals=routing["signals"],
        tokens_input=llm_result["tokens_input"],
        tokens_output=llm_result["tokens_output"],
        latency_ms=llm_result["latency_ms"],
        confidence=evaluation["confidence"],
        flags=evaluation["flags"],
    )
    
    print(f"{'='*60}\n")
    
    return ChatResponse(
        response=evaluation["response"],
        sources=sources,
        debug=debug,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    Streams response chunks, then sends a final metadata event.
    """
    query = request.query.strip()
    session_id = request.session_id
    
    # Retrieve + Route (same as standard endpoint)
    retrieved = retrieve(query, faiss_index, chunk_metadata)
    routing = classify_query(query)
    
    context = "\n\n".join(
        f"[Source: {c['document_name']}, Chunk #{c['chunk_id']}, "
        f"Similarity: {c['similarity_score']}]\n{c['text']}"
        for c in retrieved
    ) if retrieved else "No relevant documentation found."
    
    history = _get_history(session_id)
    
    async def event_generator():
        full_response = ""
        final_meta = {}
        
        for item in chat_completion_stream(
            model=routing["model_used"],
            context=context,
            query=query,
            conversation_history=history,
        ):
            if "chunk" in item:
                yield {"event": "chunk", "data": json.dumps({"text": item["chunk"]})}
            elif item.get("done"):
                full_response = item.get("response", "")
                final_meta = item
        
        # Evaluate
        evaluation = evaluate_response(full_response, retrieved)
        
        # Log
        log_request(
            query=query,
            classification=routing["classification"],
            model_used=routing["model_used"],
            tokens_input=final_meta.get("tokens_input", 0),
            tokens_output=final_meta.get("tokens_output", 0),
            latency_ms=final_meta.get("latency_ms", 0),
            confidence=evaluation["confidence"],
            flags=evaluation["flags"],
            num_sources=len(retrieved),
        )
        
        # Update memory
        _update_history(session_id, query, full_response)
        
        # Send final metadata event
        sources = [
            {
                "chunk_id": c["chunk_id"],
                "document_name": c["document_name"],
                "similarity_score": c["similarity_score"],
            }
            for c in retrieved
        ]
        
        meta = {
            "sources": sources,
            "debug": {
                "classification": routing["classification"],
                "model_used": routing["model_used"],
                "complex_score": routing["complex_score"],
                "signals": routing["signals"],
                "tokens_input": final_meta.get("tokens_input", 0),
                "tokens_output": final_meta.get("tokens_output", 0),
                "latency_ms": final_meta.get("latency_ms", 0),
                "confidence": evaluation["confidence"],
                "flags": evaluation["flags"],
            },
        }
        yield {"event": "metadata", "data": json.dumps(meta)}
        yield {"event": "done", "data": "{}"}
    
    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "index_size": faiss_index.ntotal if faiss_index else 0,
        "chunks_loaded": len(chunk_metadata) if chunk_metadata else 0,
    }
