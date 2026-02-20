"""
Structured JSON logger for the Clearpath chatbot.
Appends one JSON object per request to logs/logs.json.
"""
import json
import os
from datetime import datetime, timezone

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOGS_FILE = os.path.join(LOGS_DIR, "logs.json")


def log_request(
    query: str,
    classification: str,
    model_used: str,
    tokens_input: int,
    tokens_output: int,
    latency_ms: float,
    confidence: str,
    flags: list[str],
    num_sources: int,
):
    """
    Append a structured log entry to logs.json.
    
    Each entry is a JSON object appended to a JSON array file.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "classification": classification,
        "model_used": model_used,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "latency_ms": latency_ms,
        "confidence": confidence,
        "flags": flags,
        "num_sources": num_sources,
    }
    
    # Read existing log entries
    entries = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    entries = json.loads(content)
        except (json.JSONDecodeError, IOError):
            entries = []
    
    entries.append(entry)
    
    with open(LOGS_FILE, "w") as f:
        json.dump(entries, f, indent=2)
    
    print(f"  Logger: logged request (total entries: {len(entries)})")
