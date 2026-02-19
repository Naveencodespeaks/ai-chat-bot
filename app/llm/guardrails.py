# app/llm/guardrails.py
from typing import Dict, Any, List, Tuple

def enforce_guardrails(
    user_message: str,
    assistant_message: str,
    user_context: Dict[str, Any],
) -> Tuple[str, List[str]]:
    """
    Minimal guardrails:
    - remove accidental secrets
    - avoid hallucinated credentials
    Expand later with PII masking, compliance, etc.
    """
    flags: List[str] = []
    reply = assistant_message or ""

    # Example: block API key patterns (very basic)
    if "sk-" in reply:
        reply = "I can’t share sensitive keys or credentials. Please contact IT Admin."
        flags.append("secret_leak_prevented")

    return reply, flags
