"""
Clearpath RAG Chatbot — FastAPI Backend
POST /query — API contract endpoint (question/conversation_id)
POST /chat — Legacy chat endpoint
POST /chat/stream — SSE streaming endpoint
"""
import os
import json
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI
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

# Conversation memory: conversation_id → list of last N user/assistant pairs
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

# API Contract models (POST /query)
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None


class TokensInfo(BaseModel):
    input: int
    output: int


class QueryMetadata(BaseModel):
    model_used: str
    classification: str
    tokens: TokensInfo
    latency_ms: int
    chunks_retrieved: int
    evaluator_flags: list[str]


class SourceInfo(BaseModel):
    document: str
    page: int | None = None
    relevance_score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    metadata: QueryMetadata
    sources: list[SourceInfo]
    conversation_id: str


# Legacy models for /chat/stream (used by frontend SSE)
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")


# ─── Helpers ────────────────────────────────────────────────────────────
def _get_history(conv_id: str) -> list[dict]:
    return list(conversation_memory[conv_id])


def _update_history(conv_id: str, question: str, answer: str):
    history = conversation_memory[conv_id]
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    if len(history) > MAX_MEMORY * 2:
        conversation_memory[conv_id] = history[-(MAX_MEMORY * 2):]


def _run_pipeline(question: str, conv_id: str):
    """Shared pipeline logic for both /query and /chat endpoints."""
    retrieved = retrieve(question, faiss_index, chunk_metadata)
    routing = classify_query(question)

    context = "\n\n".join(
        f"[Source: {c['document_name']}, Chunk #{c['chunk_id']}, "
        f"Similarity: {c['similarity_score']}]\n{c['text']}"
        for c in retrieved
    ) if retrieved else "No relevant documentation found."

    history = _get_history(conv_id)
    llm_result = chat_completion(
        model=routing["model_used"],
        context=context,
        query=question,
        conversation_history=history,
    )

    evaluation = evaluate_response(llm_result["response"], retrieved)

    log_request(
        query=question,
        classification=routing["classification"],
        model_used=routing["model_used"],
        tokens_input=llm_result["tokens_input"],
        tokens_output=llm_result["tokens_output"],
        latency_ms=llm_result["latency_ms"],
        confidence=evaluation["confidence"],
        flags=evaluation["flags"],
        num_sources=len(retrieved),
    )

    _update_history(conv_id, question, evaluation["response"])

    return {
        "retrieved": retrieved,
        "routing": routing,
        "llm_result": llm_result,
        "evaluation": evaluation,
    }


# ─── POST /query — API Contract Endpoint ────────────────────────────────
@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    API contract endpoint matching the assignment spec.
    POST /query with {question, conversation_id?}
    """
    question = request.question.strip()
    conv_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:8]}"

    print(f"\n{'='*60}")
    print(f"  Query: {question}")
    print(f"  Conversation: {conv_id}")

    result = _run_pipeline(question, conv_id)

    sources = [
        SourceInfo(
            document=c["document_name"],
            page=None,
            relevance_score=c["similarity_score"],
        )
        for c in result["retrieved"]
    ]

    metadata = QueryMetadata(
        model_used=result["routing"]["model_used"],
        classification=result["routing"]["classification"],
        tokens=TokensInfo(
            input=result["llm_result"]["tokens_input"],
            output=result["llm_result"]["tokens_output"],
        ),
        latency_ms=int(result["llm_result"]["latency_ms"]),
        chunks_retrieved=len(result["retrieved"]),
        evaluator_flags=result["evaluation"]["flags"],
    )

    print(f"{'='*60}\n")

    return QueryResponse(
        answer=result["evaluation"]["response"],
        metadata=metadata,
        sources=sources,
        conversation_id=conv_id,
    )


# ─── POST /chat — Legacy endpoint (used by frontend) ───────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    """Legacy /chat endpoint maintained for frontend compatibility."""
    question = request.query.strip()
    conv_id = request.session_id

    result = _run_pipeline(question, conv_id)

    return {
        "response": result["evaluation"]["response"],
        "sources": [
            {
                "document": c["document_name"],
                "chunk_id": c["chunk_id"],
                "document_name": c["document_name"],
                "similarity_score": c["similarity_score"],
            }
            for c in result["retrieved"]
        ],
        "debug": {
            "classification": result["routing"]["classification"],
            "model_used": result["routing"]["model_used"],
            "complex_score": result["routing"]["complex_score"],
            "signals": result["routing"]["signals"],
            "tokens_input": result["llm_result"]["tokens_input"],
            "tokens_output": result["llm_result"]["tokens_output"],
            "latency_ms": result["llm_result"]["latency_ms"],
            "confidence": result["evaluation"]["confidence"],
            "flags": result["evaluation"]["flags"],
        },
    }


# ─── POST /chat/stream — SSE Streaming ─────────────────────────────────
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming endpoint for the frontend."""
    question = request.query.strip()
    conv_id = request.session_id

    retrieved = retrieve(question, faiss_index, chunk_metadata)
    routing = classify_query(question)

    context = "\n\n".join(
        f"[Source: {c['document_name']}, Chunk #{c['chunk_id']}, "
        f"Similarity: {c['similarity_score']}]\n{c['text']}"
        for c in retrieved
    ) if retrieved else "No relevant documentation found."

    history = _get_history(conv_id)

    async def event_generator():
        full_response = ""
        final_meta = {}

        for item in chat_completion_stream(
            model=routing["model_used"],
            context=context,
            query=question,
            conversation_history=history,
        ):
            if "chunk" in item:
                yield {"event": "chunk", "data": json.dumps({"text": item["chunk"]})}
            elif item.get("done"):
                full_response = item.get("response", "")
                final_meta = item

        evaluation = evaluate_response(full_response, retrieved)

        log_request(
            query=question,
            classification=routing["classification"],
            model_used=routing["model_used"],
            tokens_input=final_meta.get("tokens_input", 0),
            tokens_output=final_meta.get("tokens_output", 0),
            latency_ms=final_meta.get("latency_ms", 0),
            confidence=evaluation["confidence"],
            flags=evaluation["flags"],
            num_sources=len(retrieved),
        )

        _update_history(conv_id, question, full_response)

        sources = [
            {
                "document": c["document_name"],
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


# ─── Health Check ───────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "index_size": faiss_index.ntotal if faiss_index else 0,
        "chunks_loaded": len(chunk_metadata) if chunk_metadata else 0,
    }
