# Clearpath RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** customer support chatbot for **Clearpath**, a fictional SaaS project management platform.

Built with **FastAPI**, **Groq LLMs**, **FAISS**, and a **React/Vite** frontend styled like ChatGPT.

---

## How It Works

```
User Query → RAG Retrieval → Model Router → Groq LLM → Evaluator → Response
                  ↑                                          ↓
            FAISS Index                                Quality Checks
         (30 Clearpath docs)                      (hallucination, refusal,
                                                   unsourced pricing)
```

### Three-Layer Pipeline

| Layer       | Component    | Description                                                                              |
| ----------- | ------------ | ---------------------------------------------------------------------------------------- |
| **Layer 1** | RAG Pipeline | PDF ingestion → 500-token chunking → FAISS vector search → top-5 retrieval               |
| **Layer 2** | Model Router | 9-signal scoring classifier routes to 8B (simple) or 70B (complex)                       |
| **Layer 3** | Evaluator    | 5 checks: no-context, refusal, keyword hallucination, context-overlap, unsourced pricing |

---

## Quick Start

> **Full setup instructions →** [SETUP.md](SETUP.md)

```bash
# 1. Setup
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
echo "GROQ_API_KEY=your_key" > .env

# 2. Start backend
cd backend && uvicorn main:app --port 8000 --reload

# 3. Start frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**

---

## Groq Models

| Classification | Model                     | Use Case                                           |
| -------------- | ------------------------- | -------------------------------------------------- |
| Simple         | `llama-3.1-8b-instant`    | Greetings, single-fact lookups, yes/no             |
| Complex        | `llama-3.3-70b-versatile` | Multi-step questions, comparisons, troubleshooting |

### Router — 9 Scoring Signals

```
complex_score = 0
+2  word count ≥ 20           (long query)
+2  reasoning keywords         (explain, compare, why, how, recommend...)
+1  comparison patterns        (vs, versus, "difference between", "which plan")
+1  complaint/issue keywords   (not working, broken, error, bug, crash...)
+1  multiple question marks    (multi-part question)
+1  multi-sentence (≥ 3)       (complex context)
-2  word count < 8             (short = simple)
-2  greeting detected          (hi, hello, hey)
-1  yes/no pattern             (yes, no, sure, okay)

→ "complex" if score ≥ 2, else "simple"
```

### Evaluator — 5 Quality Checks

| #   | Check                   | Trigger                                               | Flag                      |
| --- | ----------------------- | ----------------------------------------------------- | ------------------------- |
| 1   | No context              | Zero relevant chunks retrieved                        | `no_context`              |
| 2   | Refusal                 | Response contains "I don't know", "I cannot", etc.    | `refusal_detected`        |
| 3   | Hallucination (keyword) | Out-of-domain terms: blockchain, quantum, NFT...      | `hallucination_keyword`   |
| 4   | Hallucination (overlap) | Response content diverges from context (<30% overlap) | `potential_hallucination` |
| 5   | Unsourced pricing       | Dollar amounts in response not found in source docs   | `unsourced_pricing`       |

When flagged → UI shows: **"⚠ Low confidence — please verify with support"**

---

## Eval Harness

Run the built-in evaluation suite to validate routing, retrieval, and evaluator behavior:

```bash
cd backend
python eval_harness.py
```

**14 test cases** covering:

- **Routing (5):** Greetings → simple, reasoning → complex, complaints → complex, yes/no → simple
- **Retrieval (3):** Keyboard shortcuts doc retrieved, pricing doc retrieved, off-topic → no results
- **Evaluator (3):** Blockchain → hallucination flag, quantum → hallucination, off-topic → low confidence
- **End-to-end (2):** Integration answer includes "slack", password answer includes "password"

Results saved to `eval_results.json` with per-test pass/fail, classification, model, confidence, and flags.

---

## Project Structure

```
clearpath-chatbot/
├── .env                         # GROQ_API_KEY (not committed)
├── README.md
├── SETUP.md                     # Setup instructions
├── written_answers.md           # Q1-Q4 written answers
├── docs/                        # 30 Clearpath PDF documents
├── data/                        # Auto-generated FAISS index + chunks (gitignored)
├── backend/
│   ├── main.py                  # FastAPI app (/query, /chat, /chat/stream)
│   ├── eval_harness.py          # 14-test evaluation suite
│   ├── requirements.txt
│   ├── rag/
│   │   ├── ingest.py            # PDF text extraction (PyPDF2)
│   │   ├── chunk.py             # 500-token chunking, 100-token overlap
│   │   ├── embed.py             # all-MiniLM-L6-v2 embeddings + FAISS
│   │   └── retrieve.py          # Top-5 retrieval with similarity threshold
│   ├── router/router.py         # 9-signal scoring classifier
│   ├── evaluator/evaluator.py   # 5-check response quality evaluator
│   ├── llm/groq_client.py       # Groq API wrapper (standard + streaming)
│   └── logs/logger.py           # Structured JSON logging
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── App.jsx              # Multi-conversation state + SSE streaming
        ├── index.css            # Tailwind v4 + dark theme tokens
        └── components/
            ├── Sidebar.jsx      # Chat list sidebar
            ├── MainLayout.jsx   # Layout composition
            ├── Header.jsx       # Model indicator + debug toggle
            ├── ChatWindow.jsx   # Centered messages + suggestion chips
            ├── ChatMessage.jsx  # Markdown rendering + confidence labels
            ├── ChatInput.jsx    # Auto-resize textarea
            └── DebugPanel.jsx   # Model, tokens, flags, sources
```

---

## API Endpoints

### `POST /query` — Assignment API Contract

```json
// Request
{ "question": "What are the pricing plans?", "conversation_id": "optional" }

// Response
{
  "answer": "...",
  "metadata": {
    "model_used": "llama-3.3-70b-versatile",
    "classification": "complex",
    "tokens": { "input": 1234, "output": 156 },
    "latency_ms": 847,
    "chunks_retrieved": 5,
    "evaluator_flags": []
  },
  "sources": [{ "document": "14_Pricing_Sheet_2024.pdf", "relevance_score": 0.92 }],
  "conversation_id": "conv_abc123"
}
```

### `POST /chat/stream` — SSE Streaming (Frontend)

### `GET /health` — Health Check

---

## Design Decisions

1. **FAISS** — Zero external dependencies, fast for 30 documents, persisted to disk
2. **9-signal scoring router** — Deterministic, zero-latency, transparent signal breakdown logged per request
3. **5-check evaluator** — Comprehensive: no-context, refusal, keyword hallucination, context-overlap, and domain-specific unsourced pricing
4. **Cosine similarity threshold (0.25)** — Permissive to avoid zero-result queries; evaluator catches worst cases
5. **Strict grounding prompt** — LLM refuses rather than hallucinating
6. **Eval harness** — 14 automated test cases for regression testing

---

## Bonus Challenges

| Challenge           | Status                                                |
| ------------------- | ----------------------------------------------------- |
| Conversation memory | ✅ Last 3 turns per session                           |
| Streaming           | ✅ SSE token-by-token with fallback                   |
| Eval harness        | ✅ 14 test cases (routing, retrieval, evaluator, E2E) |

---

## Known Limitations

1. Similarity threshold (0.25) can retrieve marginally relevant chunks
2. No temporal awareness — treats all documents as equally current
3. No cross-encoder re-ranking step after FAISS retrieval
