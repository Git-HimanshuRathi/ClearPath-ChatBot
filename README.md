# Clearpath RAG Chatbot

A production-quality **Retrieval-Augmented Generation (RAG)** chatbot for **Clearpath**, a fictional SaaS project management platform. Built with FastAPI, Groq LLMs, FAISS vector search, and a React/Vite frontend.

![Architecture](https://img.shields.io/badge/Architecture-RAG-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-purple) ![LLM](https://img.shields.io/badge/LLM-Groq-orange)

---

## 🏗️ Architecture

```
User Query → [RAG Retrieval] → [Model Router] → [Groq LLM] → [Evaluator] → Response
                  ↑                                                ↓
            FAISS Index                                     Quality Checks
          (Clearpath docs)                              (hallucination, refusal)
```

### Three-Layer Pipeline

| Layer       | Component    | Description                                                                    |
| ----------- | ------------ | ------------------------------------------------------------------------------ |
| **Layer 1** | RAG Pipeline | PDF ingestion → token chunking → FAISS indexing → top-5 retrieval              |
| **Layer 2** | Model Router | Scoring-based classifier routes to 8B (simple) or 70B (complex) models         |
| **Layer 3** | Evaluator    | Detects no-context, refusal, keyword hallucination, and context-overlap issues |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (tested with 3.13)
- Node.js 18+
- A valid [Groq API key](https://console.groq.com/)

### 1. Clone & Setup Environment

```bash
cd clearpath-chatbot

# Create Python virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

```bash
# Edit .env and add your Groq API key
echo "GROQ_API_KEY=your_actual_key_here" > .env
```

### 3. Generate Sample PDFs (if not present)

```bash
pip install reportlab
python generate_docs.py
```

### 4. Start Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup, the server will:

- Ingest PDFs from `docs/`
- Chunk text into 500-token windows
- Generate embeddings with `all-MiniLM-L6-v2`
- Build and persist the FAISS index to `data/`

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📁 Project Structure

```
clearpath-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app (/chat, /chat/stream, /health)
│   ├── requirements.txt
│   ├── rag/
│   │   ├── ingest.py            # PDF text extraction (PyPDF2)
│   │   ├── chunk.py             # 500-token chunking with 100-token overlap
│   │   ├── embed.py             # Embedding + FAISS with L2 normalization
│   │   └── retrieve.py          # Top-5 retrieval with threshold + LRU cache
│   ├── router/
│   │   └── router.py            # Scoring-based model classifier
│   ├── evaluator/
│   │   └── evaluator.py         # Response quality evaluator
│   ├── llm/
│   │   └── groq_client.py       # Groq API wrapper (standard + streaming)
│   └── logs/
│       └── logger.py            # Structured JSON logging
├── frontend/
│   └── src/
│       ├── App.jsx              # Main chat UI with SSE streaming
│       ├── components/
│       │   ├── ChatWindow.jsx   # Message bubbles + source citations
│       │   ├── ChatInput.jsx    # Input box + send button
│       │   └── DebugPanel.jsx   # Debug sidebar (model, tokens, confidence)
│       ├── App.css              # Dark theme + glassmorphism styles
│       └── index.css            # Global design tokens
├── docs/                        # Sample Clearpath PDFs
├── data/                        # Persisted FAISS index (auto-generated)
├── .env                         # GROQ_API_KEY
├── README.md
└── written_answers.md
```

---

## 🔧 Improvements Implemented

| #   | Improvement                         | Location                           | Impact                                           |
| --- | ----------------------------------- | ---------------------------------- | ------------------------------------------------ |
| 1   | FAISS persistence to disk           | `embed.py`, `main.py`              | Eliminates re-indexing on restart                |
| 2   | Explicit `faiss.normalize_L2()`     | `embed.py`, `retrieve.py`          | True cosine similarity via IndexFlatIP           |
| 3   | Similarity threshold (0.25)         | `retrieve.py`                      | Filters irrelevant low-score chunks              |
| 4   | Context-overlap hallucination check | `evaluator.py`                     | Catches responses diverging from context         |
| 5   | Strict grounding system prompt      | `groq_client.py`                   | Constrains LLM to documentation only             |
| 6   | Scoring-based router                | `router.py`                        | Multi-signal classification with score breakdown |
| 7   | Retrieval metadata in response      | `retrieve.py`, `main.py`, frontend | Full transparency with sources + scores          |
| 8   | Query embedding LRU cache           | `retrieve.py`                      | Avoids redundant embedding for repeated queries  |

---

## 🤖 Model Routing

The router uses a **scoring-based classification** system:

```
complex_score = 0
+2  if word_count > 20
+2  if contains reasoning keywords
+1  if multiple question marks
+1  if multi-sentence query
-2  if word_count < 12
-2  if greeting detected
-1  if yes/no response

→ "complex" if score ≥ 3, else "simple"
```

| Classification | Model                     | Best For                                        |
| -------------- | ------------------------- | ----------------------------------------------- |
| Simple         | `llama-3.1-8b-instant`    | Greetings, short questions, yes/no              |
| Complex        | `llama-3.3-70b-versatile` | Multi-part questions, analysis, troubleshooting |

---

## 📊 API Endpoints

### `POST /chat`

Standard chat with full response.

```json
{
  "query": "What are the pricing plans?",
  "session_id": "user-123"
}
```

### `POST /chat/stream`

Server-Sent Events streaming.

### `GET /health`

Health check returning index stats.

---

## 📝 Design Decisions

1. **FAISS over ChromaDB**: Chosen for simplicity, zero external dependencies, and predictable performance with small document sets.
2. **Scoring router over LLM classifier**: Deterministic, zero-latency classification with transparent signal breakdown — no additional API calls needed.
3. **Cosine similarity threshold (0.25)**: Prevents returning irrelevant chunks when the query is off-topic, which the evaluator then flags as `no_context`.
4. **Strict grounding prompt**: The system prompt explicitly instructs the LLM to refuse rather than hallucinate, working in tandem with the evaluator's refusal detection.
5. **LRU cache for embeddings**: Particularly effective in customer support where the same questions are asked repeatedly (FAQs).

---

## 📄 License

This project is for educational/demonstration purposes.
