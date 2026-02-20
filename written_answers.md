# Written Answers — Clearpath RAG Chatbot

---

## Q1: How does your model router classify queries, and what are the boundary conditions where it might misclassify?

The model router employs a **scoring-based deterministic classification** system rather than a simple keyword if/else approach. Each incoming query is evaluated against seven binary signals that increment or decrement a `complex_score`. Positive signals include: long query (word count > 20, +2), presence of reasoning keywords like "explain", "compare", or "troubleshoot" (+2), multiple question marks (+1), and multi-sentence structure (+1). Negative signals include: short query (word count < 12, -2), greeting patterns like "hi" or "hello" (-2), and yes/no responses (-1). If the cumulative score reaches 3 or above, the query is classified as "complex" and routed to `llama-3.3-70b-versatile`; otherwise it goes to `llama-3.1-8b-instant`.

The primary **boundary condition for misclassification** occurs with edge-case queries that are semantically complex but syntactically simple. For example, "Why is SSO failing?" is a short 4-word query (triggering -2) with one reasoning keyword (+2), yielding a score of 0 — classified as "simple" despite requiring deep troubleshooting analysis. Conversely, a long greeting like "Hello, I hope you're having a wonderful day, I just wanted to say thank you for your excellent product and amazing support team" would score +2 for length despite being trivially simple. The scoring system trades perfect classification for determinism, transparency, and zero additional API latency — a deliberate design choice where the debugging visibility (score breakdown + signals) outweighs marginal accuracy gains from an LLM-based classifier.

---

## Q2: Explain your RAG retrieval strategy and how it handles the case where no relevant documents are found.

The retrieval strategy operates as a multi-step pipeline: First, the user query is embedded using `all-MiniLM-L6-v2` (a 384-dimensional sentence transformer model). The embedding is **explicitly L2-normalized** using `faiss.normalize_L2()`, ensuring that inner product search in the FAISS `IndexFlatIP` index yields true cosine similarity scores. The index then returns the top-5 nearest neighbors with their similarity scores.

The critical **threshold filter (Improvement 3)** then discards any chunks scoring below 0.25 cosine similarity. This is essential because FAISS always returns K results regardless of actual relevance — without the threshold, off-topic queries like "Tell me about blockchain" would still receive 5 chunks about Clearpath, leading the LLM to fabricate connections between irrelevant context and the query.

When **no chunks survive the threshold filter**, the system returns an empty retrieval list. This triggers a cascade of safety mechanisms: (1) the context passed to the LLM reads "No relevant documentation found", (2) the strict grounding system prompt instructs the LLM to refuse rather than guess, and (3) the evaluator flags the response with `no_context`, setting confidence to "low". This three-layer defense — retrieval threshold, grounding prompt, evaluator flag — ensures the system gracefully handles out-of-scope queries rather than hallucinating answers.

An **LRU cache (Improvement 8)** stores up to 128 recent query embeddings, keyed by normalized query text. This avoids redundant embedding computation for repeated questions, which is particularly valuable in customer support contexts where FAQ-style queries recur frequently.

---

## Q3: If you could add one optimization to improve production readiness, what would it be and why?

The highest-ROI optimization would be **implementing query embedding caching with a persistent Redis backend** alongside semantic deduplication. While the current LRU cache (Improvement 8) avoids redundant embedding computation within a single server process, it is lost on restart and isolated per worker process. In production, customer support workloads exhibit a **Zipfian distribution** — a small set of common questions ("How do I reset my password?", "What are the pricing plans?") accounts for a disproportionate share of total queries.

A persistent cache with **semantic deduplication** would: (1) embed the query, (2) search the cache for semantically similar past queries (cosine similarity > 0.95), (3) if found, return the cached retrieval results and even cached LLM responses directly, bypassing the entire pipeline. This would reduce both Groq API costs (which scale linearly with requests) and p99 latency from ~2s to ~50ms for cached queries. Implementation would involve Redis with a secondary FAISS index over cached query embeddings, with TTL-based expiration and cache invalidation when the document index is rebuilt.

This single optimization addresses three production concerns simultaneously: **cost** (fewer LLM API calls), **latency** (sub-100ms for cache hits), and **scalability** (reduces load on the Groq API rate limit of 1,000-5,000 req/min). It also enables offline analytics on query patterns, informing documentation improvements for the most-asked questions.

---

## Q4: Describe how the evaluator detects potential hallucinations and what its limitations are.

The evaluator implements a **two-pronged hallucination detection** strategy. The first mechanism is a **keyword blacklist** — it checks if the LLM response contains out-of-domain terms like "blockchain", "cryptocurrency", "NFT", or "quantum" that should never appear in Clearpath documentation context. This catches obvious cases where the model generates content from its pre-training data rather than the provided context.

The second, more sophisticated mechanism is the **context-overlap check (Improvement 4)**. It extracts non-stopword "content words" from both the LLM response and the retrieved context chunks, then computes a word-level overlap ratio. If fewer than 30% of the response's content words appear in the context, the response is flagged as `potential_hallucination`. For example, if the context discusses "sprint planning" and "task management" but the response starts discussing "machine learning workflows" and "neural networks", the overlap would drop well below 30%, triggering the flag.

The **primary limitation** is that this approach operates at the lexical level rather than the semantic level. A hallucinated response that cleverly uses the same vocabulary as the context but arranges it into factually incorrect statements would pass the overlap check. For instance, if the context says "Free plan supports 5 users" but the model responds "Free plan supports 50 users", the overlap would be high (same words) but the answer is factually wrong. Additionally, the 30% threshold is a heuristic — legitimate responses that paraphrase heavily or use synonyms (saying "cost" instead of "price") could be incorrectly flagged. Production systems would benefit from adding NLI-based (Natural Language Inference) entailment checking, where a smaller model verifies that the response is actually entailed by the context rather than merely sharing vocabulary.

---

## AI Usage Declaration

This project was developed with the assistance of AI coding tools (Claude/Anthropic). AI was used for code generation, architecture design, documentation writing, and debugging. All generated code was reviewed, tested, and validated for correctness. The conceptual architecture, design decisions, and improvement strategies reflect understanding of RAG systems, vector databases, and LLM grounding techniques.
