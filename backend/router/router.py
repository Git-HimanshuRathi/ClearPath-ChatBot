"""
Scoring-based deterministic model router.
Classifies queries as 'simple' or 'complex' using a multi-signal scoring system.
Maps: simple → llama-3.1-8b-instant, complex → llama-3.3-70b-versatile
"""
import re

# Model mapping
MODELS = {
    "simple": "llama-3.1-8b-instant",
    "complex": "llama-3.3-70b-versatile",
}

# Threshold for complex classification
COMPLEX_THRESHOLD = 3

# Reasoning keywords that suggest complex queries
REASONING_KEYWORDS = [
    "explain", "compare", "analyze", "difference", "why", "how does",
    "what happens", "describe", "elaborate", "detail", "advantages",
    "disadvantages", "trade-off", "tradeoff", "versus", "vs",
    "recommend", "suggest", "best practice", "architecture", "design",
    "strategy", "approach", "workflow", "process", "troubleshoot",
    "debug", "diagnose", "investigate", "complex", "advanced",
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
    Classify a user query using scoring-based signals.
    
    Improvement 6: Multi-signal scoring instead of simple if/else.
    
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
    if word_count > 20:
        complex_score += 2
        signals.append(f"long_query (word_count={word_count})")
    
    # Signal 2: Reasoning keywords
    reasoning_found = [kw for kw in REASONING_KEYWORDS if kw in text]
    if reasoning_found:
        complex_score += 2
        signals.append(f"reasoning_keywords ({', '.join(reasoning_found[:3])})")
    
    # Signal 3: Multiple question marks
    question_marks = text.count("?")
    if question_marks > 1:
        complex_score += 1
        signals.append(f"multiple_questions (count={question_marks})")
    
    # Signal 4: Multi-sentence
    if len(sentences) > 1:
        complex_score += 1
        signals.append(f"multi_sentence (count={len(sentences)})")
    
    # Signal 5: Short queries suggest simplicity
    if word_count < 12:
        complex_score -= 2
        signals.append(f"short_query (word_count={word_count})")
    
    # Signal 6: Greeting patterns
    is_greeting = any(re.match(pat, text) for pat in GREETING_PATTERNS)
    if is_greeting:
        complex_score -= 2
        signals.append("greeting_detected")
    
    # Signal 7: Yes/No responses
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
