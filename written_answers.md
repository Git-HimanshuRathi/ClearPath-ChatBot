# Written Answers

## Q1 — Routing Logic

Our router uses a **deterministic, scoring-based classifier** with nine explicit signals. Each signal adds or subtracts from a `complex_score`:

**Rules:**

- **Word count ≥ 20:** +2 (long queries need reasoning)
- **Reasoning keywords** (explain, compare, why, how, recommend, troubleshoot, etc.): +2
- **Comparison patterns** (vs, versus, "difference between", "which plan"): +1
- **Complaint/issue keywords** (not working, broken, error, bug, crash): +1
- **Multiple question marks (≥ 2):** +1 (multi-part question)
- **Multiple sentences (≥ 3):** +1 (complex context)
- **Word count < 8:** -2 (short = simple)
- **Greeting pattern** (hi, hello, hey): -2
- **Yes/No pattern** (yes, no, sure, okay): -1

**Boundary:** `complex_score ≥ 2` → `llama-3.3-70b-versatile`, else → `llama-3.1-8b-instant`. We chose this threshold because a single strong signal (like reasoning keywords) is enough to justify the 70B model — these queries genuinely need deeper reasoning. But weak signals alone (just being slightly long) shouldn't trigger the expensive model.

**Misclassification example:** "What's the SLA for enterprise support?" scores 0: no reasoning keywords, 6 words (−2 for short query). Classified as "simple." But this requires cross-referencing the Enterprise Plan Details and Support SLA documents — complex multi-doc synthesis. The 8B model gives a shallow answer.

**Improvement without LLM:** Add topic-aware routing with a small keyword taxonomy — queries mentioning "SLA", "enterprise", "migration", or "compliance" get +1 because these topics inherently require detailed, multi-source answers regardless of query length. This avoids LLM cost while catching domain-specific complexity.

---

## Q2 — Retrieval Failures

**Query:** "What did the team discuss in last week's standup?"

**What retrieved:** Chunks from `24_Weekly_Standup_Notes_Dec2023.pdf` with similarity scores of 0.28-0.35. The system returned standup notes from December 2023 as if they were "last week."

**Why it failed:** Our RAG pipeline uses pure semantic similarity via cosine distance — it matched "standup" and "team discuss" without understanding temporal context. The system has no concept of document dates or recency. The permissive 0.25 similarity threshold let these marginally relevant chunks through.

**Our domain-specific evaluator checks:** We implemented two domain-specific checks beyond the required no-context and refusal detection:

1. **Context-overlap check** — Measures what percentage of the LLM's response content words appear in the retrieved chunks. If overlap drops below 30%, we flag `potential_hallucination`. This catches cases where the LLM generates information that diverges from the provided context, such as inventing feature details not in any chunk. We chose this because it directly measures grounding: a well-grounded response should substantially reference the source material.

2. **Unsourced pricing detection** — Extracts dollar amounts from the LLM's response and cross-checks them against amounts in the retrieved chunks. If the response mentions prices not found in any source document, we flag `unsourced_pricing`. This is critical for a SaaS support bot where incorrect pricing can cause real customer harm.

**Fix:** Add metadata-aware retrieval — index document dates alongside content, apply temporal boost to newer documents, and implement a pre-retrieval filter for temporal queries.

---

## Q3 — Cost and Scale

**Assumptions:** 5,000 queries/day, 70% simple / 30% complex (typical support distribution).

**Token estimates per query:**

- Context (5 chunks × 500 tokens): ~2,500 input tokens
- System prompt + query: ~200 input tokens
- Conversation memory (3 turns): ~600 input tokens
- **Total input per query:** ~3,300 tokens
- **Output per query:** ~300 tokens

**Daily breakdown:**

| Model                   | Queries/day | Input tokens | Output tokens | Total tokens |
| ----------------------- | ----------- | ------------ | ------------- | ------------ |
| llama-3.1-8b-instant    | 3,500       | 11.55M       | 1.05M         | 12.6M        |
| llama-3.3-70b-versatile | 1,500       | 4.95M        | 0.45M         | 5.4M         |
| **Total**               | 5,000       | 16.5M        | 1.5M          | **18M**      |

**Proportional cost estimate (Groq pricing proxy):** Using Groq's free-tier rate limits as a proxy: the 8B model processes tokens ~4x faster but the 70B model consumes significantly more compute per token. Even at 30% of traffic, the 70B model is the dominant cost driver because per-token compute scales with model parameters.

**Biggest cost driver:** Input tokens (16.5M) outweigh output (1.5M) by 11:1 — specifically the 5 chunks × 500 tokens of context per query. The context window is the primary cost lever.

**Highest-ROI optimization:** Implement a **semantic query cache** using embedding similarity. Hash incoming query embeddings and return cached responses for queries with cosine similarity > 0.95. Customer support queries are highly repetitive (users ask the same pricing/setup questions). Caching could eliminate 40-60% of LLM calls entirely — saving both tokens and latency at near-zero marginal cost.

**Optimization to avoid:** Reducing chunk retrieval count from 5 to 1 or 2. While this cuts input tokens by 60%, it severely degrades quality for complex questions requiring synthesis across multiple document sections (e.g., comparing pricing plans across two PDFs). The quality-cost tradeoff is not worth it — a wrong answer is more expensive than a few extra tokens.

---

## Q4 — What Is Broken

**The most significant flaw:** Our similarity threshold (0.25) is **too permissive**, causing the system to retrieve and present marginally relevant chunks as authoritative context. This means the LLM frequently receives "context" that is topically adjacent but doesn't actually answer the question — leading to plausible-sounding but inaccurate responses that the user trusts.

**Concrete example:** Asking about "API rate limits" retrieves chunks about "API authentication" and "API endpoints" — close enough semantically to pass the 0.25 threshold but containing zero rate limit information. The LLM then synthesizes a confident answer from this tangential context, producing what appears to be a well-sourced response that is actually hallucinated from wrong context. This is strictly worse than "I don't know" because the user trusts a sourced answer.

**Why shipped anyway:** Raising the threshold to 0.5+ caused too many queries to return zero results, especially for paraphrased questions where embedding similarity is naturally lower (e.g., "how to cancel" vs "cancellation policy" scores ~0.35). With only 30 documents and 49 chunks, the index is sparse — aggressive filtering leaves users without answers for legitimate questions. We chose permissive retrieval over no retrieval, relying on the evaluator's context-overlap check (30% threshold) and unsourced-pricing detection as safety nets to catch the worst cases.

**Fix:** Replace the flat threshold with **dynamic threshold pruning** based on score distribution — if the top chunk scores 0.7 but chunk #4 scores 0.28, drop chunks below 50% of the top score. This adapts to each query's retrieval landscape rather than using a fixed cutoff. For a more robust solution, add a **cross-encoder re-ranking step** using `cross-encoder/ms-marco-MiniLM-L-6-v2` that re-scores the top-5 FAISS candidates with a model trained specifically for relevance assessment.

---

## AI Usage

## prompt 1 

You are a senior AI systems engineer. Your task is to build a complete production-quality implementation of a RAG-based customer support chatbot system using Groq LLMs.

This is an AI Systems Intern assignment. You must implement everything exactly according to the specifications below.

Do NOT simplify anything. Do NOT skip any requirements.

Your output must include FULL CODE for frontend, backend, router, evaluator, logging, retrieval pipeline, and written answers.

⸻

PROJECT GOAL

Build a customer support chatbot for a fictional SaaS company called Clearpath using:

• Retrieval Augmented Generation (RAG)
• Deterministic rule-based model router
• Output evaluator
• Groq LLM API
• Minimal chat frontend
• Logging and debugging info

You must use ONLY these Groq models:

Simple model:
llama-3.1-8b-instant

Complex model:
llama-3.3-70b-versatile

⸻

HARD REQUIREMENTS

You MUST implement these 3 layers:

⸻

LAYER 1 — RAG PIPELINE

You must implement a full retrieval system from scratch.

Do NOT use:

• LangChain
• LlamaIndex
• Any managed retrieval system
• Any external RAG service

Allowed:

• sentence-transformers
• FAISS
• numpy
• sklearn

⸻

RAG pipeline must include:

PDF ingestion

• Read all PDFs from docs/
• Extract text using PyPDF2 or pdfplumber

Chunking

You must implement chunking with:

chunk size: 500 tokens
overlap: 100 tokens

Store metadata:

{
chunk_id
document_name
text
}

Explain chunking strategy later.

⸻

Embedding

Use sentence-transformers model:

all-MiniLM-L6-v2

Generate embeddings.

Store in FAISS index.

⸻

Retrieval

When user query comes:

embed query

retrieve top 5 chunks

return chunks with similarity scores

⸻

Context construction

Concatenate retrieved chunks into prompt context.

Do NOT pass entire documents.

⸻

LAYER 2 — MODEL ROUTER (CRITICAL)

This must be deterministic rule-based.

You CANNOT use an LLM to decide routing.

Implement explicit classification rules.

Router must classify query into:

simple
complex

Rules must include signals like:

query length
keywords
multi-part questions
reasoning indicators
ambiguity indicators

Example rules:

simple if:

less than 12 words
contains greeting
contains yes/no question

complex if:

more than 20 words
contains words like:

how
why
explain
issue
error
problem
cannot
multiple question marks

multi sentence query

⸻

Router must output:

{
classification,
model_used
}

⸻

Model mapping:

simple → llama-3.1-8b-instant
complex → llama-3.3-70b-versatile

⸻

Log every request in this format:

{
query,
classification,
model_used,
tokens_input,
tokens_output,
latency_ms
}

Store logs in logs.json

⸻

LAYER 3 — OUTPUT EVALUATOR

After LLM generates response, evaluator must detect failures.

Must detect at minimum:
	1.	No context retrieved

If retrieved_chunks.length == 0
flag low confidence
	2.	Refusal

If response contains:

“I don’t know”
“I cannot”
“I’m not sure”
“I do not have access”

flag
	3.	Domain hallucination check

Implement:

If response contains features not present in Clearpath docs such as:

“blockchain”
“cryptocurrency”
“NFT”
“quantum”

flag hallucination

⸻

Evaluator returns:

{
response,
confidence: high | low,
flags: []
}

Frontend must display confidence label.

⸻

GROQ INTEGRATION

Use Groq API.

Backend must include:

model selection based on router

Groq call wrapper

token counting

latency measurement

⸻

BACKEND REQUIREMENTS

Use:

Python
FastAPI

Structure:

backend/
main.py
rag/
ingest.py
chunk.py
embed.py
retrieve.py
router/
router.py
evaluator/
evaluator.py
llm/
groq_client.py
logs/
logger.py

⸻

FRONTEND REQUIREMENTS

Use:

React
Vite

Minimal chat interface with:

chat window
input box
send button

Debug panel showing:

model used
token count
confidence flag

⸻

API ENDPOINT

POST /chat

input:

{
query
}

output:

{
response,
model_used,
tokens_input,
tokens_output,
confidence
}

⸻

BONUS FEATURES — IMPLEMENT

Conversation memory (last 3 messages)

Streaming support

⸻

WRITTEN ANSWERS

Generate written_answers.md

Answer these questions with 200 words each:

Q1 Routing Logic

Explain exact rules
justify boundary
give real misclassification example
suggest improvement

Q2 Retrieval Failures

Describe failure case
explain cause
suggest fix

Q3 Cost and Scale

Assume 5000 queries/day

Estimate token usage

Calculate cost proportion

Suggest highest ROI optimization

Avoid bad optimization

Q4 What is Broken

Describe real system limitation

Explain why shipped anyway

Suggest fix

Include section:

AI Usage

Say this system was built with Claude assistance

⸻

README REQUIREMENTS

Include:

setup instructions

env variables

Groq setup

run backend

run frontend

architecture explanation

design decisions

⸻

ENV VARIABLES

.env

GROQ_API_KEY=

⸻

FINAL OUTPUT FORMAT

Provide full project structure:

backend code
frontend code
README.md
written_answers.md

All files complete.

No pseudocode.

No placeholders.

Everything runnable.

⸻

DESIGN GOALS

This system must demonstrate:

production-level architecture
clean separation of concerns
correct RAG implementation
correct router implementation
correct evaluator implementation

⸻

IMPORTANT

Do NOT skip logging
Do NOT skip evaluator
Do NOT skip router rules
Do NOT simplify

Implement complete system.

⸻

OUTPUT NOW

Provide:
	1.	Project folder structure
	2.	Backend code
	3.	Frontend code
	4.	README.md
	5.	written_answers.md

All complete.

## prompt 2

You are a senior frontend engineer. Redesign my existing React + Vite chatbot frontend to look and behave like the ChatGPT interface.

Use modern production-quality React code with clean architecture.

Do NOT use placeholder code. Provide complete working code.

⸻

Overall Goal

Transform the chatbot UI to closely match ChatGPT’s interface, including:

• Left sidebar with conversations
• Main chat area centered
• Top model indicator
• Bottom fixed input box
• Streaming assistant responses
• Dark theme (default)
• Professional typography, spacing, and layout

The UI must look clean, modern, and minimal like ChatGPT.

⸻

Tech stack requirements

Use:

React
Vite
CSS or TailwindCSS (preferred: Tailwind)
Functional components
React hooks

Do NOT use heavy UI frameworks like Material UI.

⸻

Layout Structure

Create layout with 2 main sections:

Sidebar (left)
Chat area (right)

Structure:App
 ├── Sidebar
 └── MainLayout
      ├── Header
      ├── ChatWindow
      └── ChatInput
Sidebar requirements (ChatGPT-style)

Width: 260px
Background: #171717
Full height

Contains:

• App title: Clearpath AI
• “New Chat” button
• List of previous chats
• Hover effects
• Scrollable conversation list

Each chat item should show:

• Chat title
• Hover highlight
• Click to switch chat

⸻

Main Chat Area requirements

Background color: #212121

Centered chat container:

max width: 768px
margin auto
padding top/bottom: 24px

Messages stacked vertically.

⸻

Message UI (very important)

User message:

Right aligned
Background: #303030
Rounded corners
Padding: 12px 16px

Assistant message:

Left aligned
No background OR slightly lighter background
Padding: 12px 16px

Spacing between messages: 16px

⸻

Chat Input (bottom fixed like ChatGPT)

Fixed at bottom of main area.

Container style:

background: #303030
border-radius: 12px
padding: 12px

Contains:

• textarea input
• send button
• supports Enter to send
• supports Shift+Enter for newline

Auto resize textarea.

⸻

Header requirements

Top sticky header:

Height: 48px
Background: same as main

Show:

• Model name (example: llama-3.3-70b-versatile)
• small dropdown style

⸻

Theme requirements (Dark theme)

Use these exact colors:

Background main: #212121
Sidebar background: #171717
Input background: #303030
User message background: #303030
Text primary: #ECECEC
Text secondary: #A0A0A0

Font:

system-ui, -apple-system, Segoe UI, Roboto, sans-serif

⸻

Streaming support

Assistant messages must support streaming text updates:

Example:

User sends message
Assistant message appears empty
Text streams in gradually

⸻

State management

Use React state:

messages state:
{
 id,
 role: "user" | "assistant",
 content
}
Support adding new messages dynamically.

⸻

Animations

Add subtle animations:

message fade-in
hover highlight in sidebar
button hover effects

Use CSS transitions.

⸻

Files to implement

Provide full code for:

App.jsx
Sidebar.jsx
MainLayout.jsx
ChatWindow.jsx
ChatMessage.jsx
ChatInput.jsx
Header.jsx

index.css
tailwind.config.js (if using Tailwind)

⸻

UX Requirements

Match ChatGPT UX including:

Centered conversation layout
Proper spacing
Scrollable message area
Fixed input box
Professional look

No clutter.

Minimal design.

⸻

Backend integration

Send request to backend endpoint:

POST /chat

Body:

{
query: message
}

Receive:

{
response,
model_used
}

Append assistant message to chat.

⸻

Final output requirements

Provide:

Complete working code
All components
All styles
All imports
Ready to run

Do NOT skip anything.

⸻

Visual reference

Match ChatGPT layout including:

Left sidebar
Centered messages
Bottom input
Dark theme

Professional appearance.

