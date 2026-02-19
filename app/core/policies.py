# app/core/policies.py
from typing import Dict, List, Any
import re

class PolicyEngine:
    """
    Simple policy engine for v1.
    You can expand this with department policies, PII rules, jailbreak detection, etc.
    """

    def evaluate_input(self, text: str, user_context: Dict[str, Any]) -> List[str]:
        flags: List[str] = []

        t = text.lower()

        # prompt injection patterns
        if "ignore previous" in t or "system prompt" in t:
            flags.append("prompt_injection_suspected")

        # very basic unsafe blocking examples
        # (extend as per your company's policy)
        blocked_patterns = [
            r"password\s+of",
            r"steal\s+data",
            r"hack\s+",
        ]
        for pat in blocked_patterns:
            if re.search(pat, t):
                flags.append("blocked")
                break

        return flags
