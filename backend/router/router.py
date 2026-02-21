"""
Scoring-based deterministic model router.
Classifies queries as 'simple' or 'complex' using a multi-signal scoring system.
Maps: simple → llama-3.1-8b-instant, complex → llama-3.3-70b-versatile

Signals:
  +2  long query (≥20 words)
  +2  reasoning keywords (explain, compare, why, how...)
  +1  comparison pattern (vs, versus, difference between)
  +1  multiple question marks
  +1  multi-sentence (≥3 sentences)
  +1  complaint/issue indicators (error, broken, not working, bug...)
  -2  short query (<8 words)
  -2  greeting detected
  -1  yes/no response
"""
import re

# Model mapping
MODELS = {
    "simple": "llama-3.1-8b-instant",
    "complex": "llama-3.3-70b-versatile",
}

# Threshold for complex classification
COMPLEX_THRESHOLD = 2

# Reasoning keywords that suggest complex queries
REASONING_KEYWORDS = [
    "explain", "compare", "analyze", "difference", "why", "how does",
    "what happens", "describe", "elaborate", "detail", "advantages",
    "disadvantages", "trade-off", "tradeoff", "versus", "vs",
    "recommend", "suggest", "best practice", "architecture", "design",
    "strategy", "approach", "workflow", "process", "troubleshoot",
    "debug", "diagnose", "investigate", "complex", "advanced",
]

# Complaint / issue keywords (Signal 8: escalation-worthy)
COMPLAINT_KEYWORDS = [
    "not working", "broken", "bug", "crash", "error", "issue",
    "problem", "fail", "can't", "cannot", "unable", "stuck",
    "wrong", "fix", "help me", "urgent", "frustrated",
]

# Comparison patterns (Signal 9)
COMPARISON_PATTERNS = [
    r"\bvs\.?\b", r"\bversus\b", r"\bcompared?\s+to\b",
    r"\bdifference\s+between\b", r"\bwhich\s+(one|plan|option)\b",
    r"\bbetter\s+than\b", r"\bpros?\s+and\s+cons?\b",
]

# Greeting patterns
GREETING_PATTERNS = [
    r"^(hi|hello|hey|howdy|greetings|good\s*(morning|afternoon|evening)|yo|sup)\b",
]

# Yes/No indicators
YES_NO_PATTERNS = [
    r"^(yes|no|yeah|nah|yep|nope|sure|ok|okay|absolutely|definitely|correct|right)\b",
]


def classify_query(query: str) -> dict:
    """
    Classify a user query using multi-signal scoring.

    Returns:
        Dict with keys: classification, model_used, complex_score, signals
    """
    text = query.strip().lower()
    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    complex_score = 0
    signals = []

    # Signal 1: Long queries suggest complexity
    if word_count >= 20:
        complex_score += 2
        signals.append(f"long_query (word_count={word_count})")

    # Signal 2: Reasoning keywords
    reasoning_found = [kw for kw in REASONING_KEYWORDS if kw in text]
    if reasoning_found:
        complex_score += 2
        signals.append(f"reasoning_keywords ({', '.join(reasoning_found[:3])})")

    # Signal 3: Multiple question marks → multi-part question
    question_marks = text.count("?")
    if question_marks > 1:
        complex_score += 1
        signals.append(f"multiple_questions (count={question_marks})")

    # Signal 4: Multi-sentence context
    if len(sentences) >= 3:
        complex_score += 1
        signals.append(f"multi_sentence (count={len(sentences)})")

    # Signal 5: Comparison patterns
    comparison_found = any(re.search(pat, text) for pat in COMPARISON_PATTERNS)
    if comparison_found:
        complex_score += 1
        signals.append("comparison_pattern")

    # Signal 6: Complaint / issue keywords (needs careful 70B handling)
    complaint_found = [kw for kw in COMPLAINT_KEYWORDS if kw in text]
    if complaint_found:
        complex_score += 1
        signals.append(f"complaint_detected ({', '.join(complaint_found[:2])})")

    # Signal 7: Short queries suggest simplicity
    if word_count < 8:
        complex_score -= 2
        signals.append(f"short_query (word_count={word_count})")

    # Signal 8: Greeting patterns
    is_greeting = any(re.match(pat, text) for pat in GREETING_PATTERNS)
    if is_greeting:
        complex_score -= 2
        signals.append("greeting_detected")

    # Signal 9: Yes/No responses
    is_yes_no = any(re.match(pat, text) for pat in YES_NO_PATTERNS)
    if is_yes_no:
        complex_score -= 1
        signals.append("yes_no_response")

    # Final classification
    classification = "complex" if complex_score >= COMPLEX_THRESHOLD else "simple"
    model_used = MODELS[classification]

    result = {
        "classification": classification,
        "model_used": model_used,
        "complex_score": complex_score,
        "signals": signals,
    }

    print(f"  Router: '{query[:50]}...' → {classification} "
          f"(score={complex_score}, model={model_used})")

    return result
