"""
Output evaluator for Clearpath chatbot responses.
Detects:
  1. No-context responses
  2. Refusal / non-answers
  3. Hallucination — keyword blacklist (out-of-domain terms)
  4. Hallucination — context overlap divergence
  5. Contradictory pricing/numeric signals
"""
import re


# Refusal phrases indicating the model couldn't answer
REFUSAL_PHRASES = [
    "i don't know",
    "i cannot",
    "i'm not sure",
    "i do not have access",
    "i don't have enough information",
    "i'm unable to",
    "i am not sure",
    "i am unable",
    "i cannot provide",
    "i don't have information",
    "not in the documentation",
    "not mentioned in",
    "beyond my knowledge",
]

# Out-of-domain keywords that suggest hallucination
HALLUCINATION_KEYWORDS = [
    "blockchain", "cryptocurrency", "nft", "quantum", "bitcoin",
    "ethereum", "metaverse", "web3", "defi", "dao", "solana",
    "dogecoin", "mining", "token sale", "ico",
]

# Common English stopwords to exclude from overlap checks
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most",
    "other", "some", "such", "no", "only", "own", "same", "than",
    "too", "very", "just", "also", "how", "when", "where", "why",
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "up", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then",
    "once", "here", "there", "if", "because", "as", "until", "while",
    "based", "provided", "using", "used", "like", "including", "such",
    "please", "note", "however", "also", "may", "well", "per",
}

# Context overlap threshold
CONTEXT_OVERLAP_THRESHOLD = 0.30


def _extract_content_words(text: str) -> set[str]:
    """Extract non-stopword content words from text."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return {w for w in words if w not in STOPWORDS}


def _extract_prices(text: str) -> list[str]:
    """Extract price mentions like $29, $49/month, $2,500, etc."""
    return re.findall(r'\$[\d,]+(?:\.\d{2})?(?:/\w+)?', text)


def _check_contradictory_pricing(response: str, retrieved_chunks: list[dict]) -> str | None:
    """
    Domain-specific check: detect when the response mentions prices
    that don't appear in any retrieved chunk. This catches cases where
    the LLM invents pricing information not present in the documentation.
    """
    response_prices = set(_extract_prices(response))
    if not response_prices:
        return None

    # Collect all prices from retrieved context
    context_text = " ".join(chunk["text"] for chunk in retrieved_chunks)
    context_prices = set(_extract_prices(context_text))

    # Find prices in response that aren't in context
    unsourced_prices = response_prices - context_prices
    if unsourced_prices:
        return (
            f"unsourced_pricing (response mentions {', '.join(sorted(unsourced_prices))} "
            f"not found in retrieved docs)"
        )

    return None


def evaluate_response(
    response: str,
    retrieved_chunks: list[dict],
) -> dict:
    """
    Evaluate an LLM response for quality issues.

    Checks:
        1. No context: flags if no chunks were retrieved
        2. Refusal: flags if response contains refusal phrases
        3. Hallucination (keyword): flags out-of-domain terms
        4. Hallucination (context overlap): flags if response diverges from context
        5. Contradictory pricing: flags prices not present in source docs

    Returns:
        Dict with keys: response, confidence ("high"|"low"), flags (list[str])
    """
    flags = []
    response_lower = response.lower()

    # Check 1: No context available
    if len(retrieved_chunks) == 0:
        flags.append("no_context")

    # Check 2: Refusal detection
    for phrase in REFUSAL_PHRASES:
        if phrase in response_lower:
            flags.append("refusal_detected")
            break

    # Check 3: Hallucination — keyword blacklist
    found_keywords = [kw for kw in HALLUCINATION_KEYWORDS if kw in response_lower]
    if found_keywords:
        flags.append(f"hallucination_keyword ({', '.join(found_keywords)})")

    # Check 4: Hallucination — context overlap
    if retrieved_chunks:
        context_text = " ".join(chunk["text"] for chunk in retrieved_chunks)
        context_words = _extract_content_words(context_text)
        response_words = _extract_content_words(response)

        if response_words:
            overlap = response_words & context_words
            overlap_ratio = len(overlap) / len(response_words)

            if overlap_ratio < CONTEXT_OVERLAP_THRESHOLD:
                flags.append(
                    f"potential_hallucination (overlap={overlap_ratio:.1%}, "
                    f"threshold={CONTEXT_OVERLAP_THRESHOLD:.0%})"
                )

    # Check 5: Contradictory / unsourced pricing
    if retrieved_chunks:
        pricing_flag = _check_contradictory_pricing(response, retrieved_chunks)
        if pricing_flag:
            flags.append(pricing_flag)

    # Determine confidence
    confidence = "low" if flags else "high"

    result = {
        "response": response,
        "confidence": confidence,
        "flags": flags,
    }

    print(f"  Evaluator: confidence={confidence}, flags={flags}")
    return result
