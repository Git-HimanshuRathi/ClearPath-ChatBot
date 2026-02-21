"""
Eval Harness — Test queries with expected behaviors.
Run: python -m eval_harness (from backend/)

Tests the full pipeline: retrieval → routing → LLM → evaluator
Reports pass/fail for each test case.
"""
import sys
import os
import json
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from rag.ingest import ingest_pdfs
from rag.chunk import chunk_documents
from rag.embed import build_index, load_index, get_model
from rag.retrieve import retrieve
from router.router import classify_query
from evaluator.evaluator import evaluate_response
from llm.groq_client import chat_completion

# ─── Test Cases ──────────────────────────────────────────────────────────
TEST_CASES = [
    # --- Routing Tests ---
    {
        "id": "R1",
        "query": "Hi there!",
        "expect_classification": "simple",
        "expect_model": "llama-3.1-8b-instant",
        "description": "Greeting should route to simple model",
    },
    {
        "id": "R2",
        "query": "Can you explain the differences between pricing plans and recommend the best one for a startup?",
        "expect_classification": "complex",
        "expect_model": "llama-3.3-70b-versatile",
        "description": "Multi-part reasoning question should route to complex model",
    },
    {
        "id": "R3",
        "query": "What is Clearpath?",
        "expect_classification": "simple",
        "expect_model": "llama-3.1-8b-instant",
        "description": "Short factual question should route to simple model",
    },
    {
        "id": "R4",
        "query": "My account is not working and I'm getting an error when I try to log in. Can you help me troubleshoot?",
        "expect_classification": "complex",
        "expect_model": "llama-3.3-70b-versatile",
        "description": "Complaint with troubleshooting should route to complex model",
    },
    {
        "id": "R5",
        "query": "Yes",
        "expect_classification": "simple",
        "expect_model": "llama-3.1-8b-instant",
        "description": "Yes/no response should route to simple model",
    },

    # --- Retrieval Tests ---
    {
        "id": "T1",
        "query": "What are the keyboard shortcuts?",
        "expect_sources_contain": "11_Keyboard_Shortcuts",
        "description": "Should retrieve keyboard shortcuts document",
    },
    {
        "id": "T2",
        "query": "How much does the Pro plan cost?",
        "expect_sources_contain": "14_Pricing_Sheet",
        "description": "Should retrieve pricing document",
    },
    {
        "id": "T3",
        "query": "What is the weather today?",
        "expect_no_relevant_sources": True,
        "description": "Off-topic query should retrieve no relevant chunks",
    },

    # --- Evaluator Tests ---
    {
        "id": "E1",
        "query": "Does Clearpath support blockchain?",
        "expect_flag_contains": "refusal",
        "description": "Should flag as refusal or hallucination for off-topic feature",
    },
    {
        "id": "E2",
        "query": "Tell me about quantum computing integration",
        "expect_confidence": "low",
        "description": "Off-topic technology query should get low confidence",
    },
    {
        "id": "E3",
        "query": "What is the meaning of life?",
        "expect_confidence": "low",
        "description": "Completely off-topic should get low confidence",
    },

    # --- End-to-End Quality Tests ---
    {
        "id": "Q1",
        "query": "What integrations does Clearpath support?",
        "expect_sources_contain": "09_Integrations_Catalog",
        "description": "Should retrieve integrations catalog document",
    },
    {
        "id": "Q2",
        "query": "How do I reset my password?",
        "expect_answer_contains": ["password"],
        "description": "Should provide password reset info",
    },
]


def run_eval():
    """Run all test cases and report results."""
    # Load index
    print("=" * 70)
    print("  CLEARPATH EVAL HARNESS")
    print("=" * 70)

    loaded = load_index()
    if loaded:
        faiss_index, chunk_metadata = loaded
        print(f"  ✓ Loaded index: {faiss_index.ntotal} vectors")
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        docs_dir = os.path.join(base_dir, "docs")
        documents = ingest_pdfs(docs_dir)
        chunks = chunk_documents(documents)
        faiss_index, chunk_metadata = build_index(chunks)
        print(f"  ✓ Built index: {faiss_index.ntotal} vectors")

    get_model()
    print()

    results = []
    passed = 0
    failed = 0
    errors = 0

    for tc in TEST_CASES:
        tc_id = tc["id"]
        query = tc["query"]
        desc = tc["description"]

        print(f"  [{tc_id}] {desc}")
        print(f"       Query: \"{query}\"")

        try:
            # Run pipeline
            retrieved = retrieve(query, faiss_index, chunk_metadata)
            routing = classify_query(query)

            context = "\n\n".join(
                f"[Source: {c['document_name']}]\n{c['text']}"
                for c in retrieved
            ) if retrieved else "No relevant documentation found."

            llm_result = chat_completion(
                model=routing["model_used"],
                context=context,
                query=query,
            )

            evaluation = evaluate_response(llm_result["response"], retrieved)

            # Check expectations
            test_passed = True
            fail_reasons = []

            # Classification check
            if "expect_classification" in tc:
                if routing["classification"] != tc["expect_classification"]:
                    test_passed = False
                    fail_reasons.append(
                        f"Classification: expected '{tc['expect_classification']}', "
                        f"got '{routing['classification']}'"
                    )

            # Model check
            if "expect_model" in tc:
                if routing["model_used"] != tc["expect_model"]:
                    test_passed = False
                    fail_reasons.append(
                        f"Model: expected '{tc['expect_model']}', "
                        f"got '{routing['model_used']}'"
                    )

            # Source document check
            if "expect_sources_contain" in tc:
                source_names = [c["document_name"] for c in retrieved]
                target = tc["expect_sources_contain"]
                if not any(target in name for name in source_names):
                    test_passed = False
                    fail_reasons.append(
                        f"Sources: expected '{target}' in {source_names}"
                    )

            # No relevant sources check
            if tc.get("expect_no_relevant_sources"):
                if len(retrieved) > 0:
                    # Allow if scores are very low
                    max_score = max(c["similarity_score"] for c in retrieved)
                    if max_score > 0.4:
                        test_passed = False
                        fail_reasons.append(
                            f"Expected no relevant sources, got {len(retrieved)} "
                            f"(max_score={max_score})"
                        )

            # Flag check
            if "expect_flag_contains" in tc:
                flags_str = " ".join(evaluation["flags"]).lower()
                if tc["expect_flag_contains"] not in flags_str:
                    test_passed = False
                    fail_reasons.append(
                        f"Flags: expected '{tc['expect_flag_contains']}' in {evaluation['flags']}"
                    )

            # Confidence check
            if "expect_confidence" in tc:
                if evaluation["confidence"] != tc["expect_confidence"]:
                    test_passed = False
                    fail_reasons.append(
                        f"Confidence: expected '{tc['expect_confidence']}', "
                        f"got '{evaluation['confidence']}'"
                    )

            # Answer content check
            if "expect_answer_contains" in tc:
                answer_lower = llm_result["response"].lower()
                for keyword in tc["expect_answer_contains"]:
                    if keyword.lower() not in answer_lower:
                        test_passed = False
                        fail_reasons.append(
                            f"Answer missing keyword: '{keyword}'"
                        )

            if test_passed:
                print(f"       ✅ PASS")
                passed += 1
            else:
                print(f"       ❌ FAIL")
                for reason in fail_reasons:
                    print(f"          → {reason}")
                failed += 1

            results.append({
                "id": tc_id,
                "query": query,
                "description": desc,
                "passed": test_passed,
                "classification": routing["classification"],
                "model": routing["model_used"],
                "confidence": evaluation["confidence"],
                "flags": evaluation["flags"],
                "sources": [c["document_name"] for c in retrieved],
                "fail_reasons": fail_reasons if not test_passed else [],
            })

        except Exception as e:
            print(f"       ⚠️  ERROR: {e}")
            errors += 1
            results.append({
                "id": tc_id,
                "query": query,
                "description": desc,
                "passed": False,
                "error": str(e),
            })

        print()
        sys.stdout.flush()

        # Rate limit delay (Groq free tier: 30 req/min)
        if tc != TEST_CASES[-1]:
            time.sleep(3)

    # Summary
    total = len(TEST_CASES)
    print("=" * 70)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed, {errors} errors")
    print(f"  Pass rate: {passed/total*100:.0f}%")
    print("=" * 70)

    # Save results
    report_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{passed/total*100:.0f}%",
            "results": results,
        }, f, indent=2)

    print(f"\n  Results saved to: {report_path}\n")
    return passed == total


if __name__ == "__main__":
    success = run_eval()
    sys.exit(0 if success else 1)
