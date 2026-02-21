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

<!-- Add your actual prompts here -->
