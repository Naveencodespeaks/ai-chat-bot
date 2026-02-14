"""
Sentiment Analysis Rules Engine

Applies domain-specific rules and adjustments to sentiment scores:
- Negation handling (not good -> bad)
- Intensifiers (very, extremely)
- Diminishers (slightly, somewhat)
- Context-specific adjustments
- Special patterns (sarcasm detection, exclamations)
"""

import re
from typing import Dict, Optional, List, Tuple
from app.core.logging import logger


# -------------------------------------------------
# NEGATION WORDS
# -------------------------------------------------
NEGATION_WORDS = {
    "not", "no", "never", "neither", "nobody", "nothing",
    "nowhere", "none", "cannot", "can't", "won't", "wouldn't",
    "shouldn't", "doesn't", "don't", "didn't", "hasn't", "haven't",
    "isn't", "aren't", "wasn't", "weren't", "ain't", "don't",
}

# -------------------------------------------------
# INTENSIFIERS (Increase sentiment magnitude)
# -------------------------------------------------
INTENSIFIERS = {
    "very": 1.3,
    "extremely": 1.4,
    "incredibly": 1.4,
    "absolutely": 1.4,
    "definitely": 1.3,
    "really": 1.2,
    "quite": 1.15,
    "somewhat": 1.1,
    "so": 1.25,
    "too": 1.2,
    "much": 1.15,
    "many": 1.15,
}

# -------------------------------------------------
# DIMINISHERS (Decrease sentiment magnitude)
# -------------------------------------------------
DIMINISHERS = {
    "slightly": 0.85,
    "a bit": 0.8,
    "somewhat": 0.85,
    "kind of": 0.8,
    "sort of": 0.8,
    "kinda": 0.8,
    "almost": 0.85,
    "barely": 0.75,
    "hardly": 0.7,
    "just": 0.85,
}

# -------------------------------------------------
# CONTEXT-SPECIFIC RULES
# -------------------------------------------------
CONTEXT_ADJUSTMENTS = {
    "complaint": {
        "boost_negative": 1.2,
        "reduce_positive": 0.7,
    },
    "support_request": {
        "boost_negative": 1.15,
        "reduce_positive": 0.8,
    },
    "feedback": {
        "boost_positive": 1.1,
        "boost_negative": 1.1,
    },
    "product_review": {
        "boost_extremes": 1.2,
    },
    "customer_service": {
        "boost_positive": 1.15,
    },
}

# -------------------------------------------------
# ESCALATION TRIGGERS
# -------------------------------------------------
ESCALATION_KEYWORDS = {
    "angry": ("angry", "furious", "enraged", "outraged"),
    "urgent": ("urgent", "asap", "immediately", "emergency", "critical"),
    "complaint": ("complaint", "complain", "issue", "problem", "broken"),
    "refund": ("refund", "money back", "return", "cancel", "charge"),
}

# -------------------------------------------------
# SARCASM PATTERNS
# -------------------------------------------------
SARCASM_PATTERNS = [
    r"yeah\s+right",
    r"sure\s+.*sure",
    r"oh\s+great",
    r"wonderful",
    r"fantastic",
    r"brilliant",
]

# -------------------------------------------------
# EMPHASIS PATTERNS
# -------------------------------------------------
EMPHASIS_PATTERNS = {
    "all_caps": r"[A-Z]{3,}",  # 3+ capital letters
    "repeated_chars": r"(.)\1{2,}",  # zzz, !!!
    "multiple_exclamations": r"!{2,}",
    "multiple_questions": r"\?{2,}",
}


class SentimentRulesEngine:
    """
    Applies linguistic and domain-specific rules to adjust sentiment scores.
    """
    
    def __init__(self):
        """Initialize the rules engine."""
        logger.info("SentimentRulesEngine initialized")
    
    def apply_rules(
        self,
        score: float,
        text: str,
        context: Optional[str] = None
    ) -> float:
        """
        Apply sentiment rules to adjust score.
        
        Args:
            score: Initial sentiment score (0-1)
            text: Original text
            context: Optional context
        
        Returns:
            Adjusted sentiment score (0-1)
        """
        try:
            adjusted_score = score
            
            # Apply negation rules
            adjusted_score = self._apply_negation_rules(adjusted_score, text)
            
            # Apply intensifiers/diminishers
            adjusted_score = self._apply_modifiers(adjusted_score, text)
            
            # Apply emphasis rules
            adjusted_score = self._apply_emphasis(adjusted_score, text)
            
            # Check for sarcasm
            adjusted_score = self._apply_sarcasm_rules(adjusted_score, text)
            
            # Apply context-specific adjustments
            if context:
                adjusted_score = self._apply_context_rules(
                    adjusted_score,
                    text,
                    context
                )
            
            # Clamp to 0-1 range
            adjusted_score = max(0.0, min(1.0, adjusted_score))
            
            return adjusted_score
        except Exception as e:
            logger.error(f"Error applying sentiment rules: {str(e)}")
            return score
    
    @staticmethod
    def _apply_negation_rules(score: float, text: str) -> float:
        """
        Handle negation patterns.
        
        Inverts sentiment when negation precedes sentiment words.
        """
        # Look for negation patterns
        negation_pattern = r'\b(?:' + '|'.join(NEGATION_WORDS) + r')\s+'
        
        if re.search(negation_pattern, text, re.IGNORECASE):
            # Flip sentiment (0.7 -> 0.3, 0.3 -> 0.7)
            inverted_score = 1.0 - score
            
            # Weighted flip (don't completely invert)
            adjusted_score = score * 0.7 + inverted_score * 0.3
            return adjusted_score
        
        return score
    
    @staticmethod
    def _apply_modifiers(score: float, text: str) -> float:
        """
        Apply intensifiers and diminishers.
        
        Modifies the magnitude of sentiment.
        """
        adjusted_score = score
        
        # Apply intensifiers
        for intensifier, multiplier in INTENSIFIERS.items():
            if re.search(rf'\b{intensifier}\b', text, re.IGNORECASE):
                # Intensify: move away from neutral (0.5)
                if score > 0.5:
                    adjusted_score = 0.5 + (score - 0.5) * multiplier
                else:
                    adjusted_score = 0.5 - (0.5 - score) * multiplier
                break
        
        # Apply diminishers
        for diminisher, multiplier in DIMINISHERS.items():
            if re.search(rf'\b{diminisher}\b', text, re.IGNORECASE):
                # Diminish: move toward neutral (0.5)
                adjusted_score = 0.5 + (adjusted_score - 0.5) * multiplier
                break
        
        return adjusted_score
    
    @staticmethod
    def _apply_emphasis(score: float, text: str) -> float:
        """
        Apply emphasis pattern rules.
        
        Amplifies sentiment based on caps, repeated chars, etc.
        """
        adjusted_score = score
        
        # Check for ALL CAPS
        if re.search(EMPHASIS_PATTERNS["all_caps"], text):
            # Amplify: 20% more extreme
            adjusted_score = 0.5 + (score - 0.5) * 1.2
        
        # Check for repeated characters (!!!!, zzz)
        if re.search(EMPHASIS_PATTERNS["repeated_chars"], text):
            # Amplify: 15% more extreme
            adjusted_score = 0.5 + (score - 0.5) * 1.15
        
        # Check for multiple exclamations
        exclamation_count = len(re.findall(r'!', text))
        if exclamation_count > 2:
            # Amplify positive sentiment, amplify intensity of negative
            if score > 0.5:
                adjusted_score = 0.5 + (score - 0.5) * 1.25
            else:
                adjusted_score = 0.5 - (0.5 - score) * 1.15
        
        # Check for multiple question marks
        question_count = len(re.findall(r'\?', text))
        if question_count > 2:
            # Decrease confidence in sentiment (move toward neutral)
            adjusted_score = 0.5 + (score - 0.5) * 0.8
        
        return adjusted_score
    
    @staticmethod
    def _apply_sarcasm_rules(score: float, text: str) -> float:
        """
        Detect and handle sarcasm patterns.
        
        Inverts sentiment if sarcasm is detected.
        """
        lower_text = text.lower()
        
        for pattern in SARCASM_PATTERNS:
            if re.search(pattern, lower_text):
                # Likely sarcasm - invert sentiment
                inverted = 1.0 - score
                # Soft inversion (don't go too extreme)
                return score * 0.5 + inverted * 0.5
        
        return score
    
    @staticmethod
    def _apply_context_rules(
        score: float,
        text: str,
        context: str
    ) -> float:
        """
        Apply context-specific sentiment adjustments.
        
        Args:
            score: Current sentiment score
            text: Original text
            context: Context identifier
        
        Returns:
            Adjusted score based on context
        """
        context = context.lower()
        adjustments = CONTEXT_ADJUSTMENTS.get(context, {})
        
        if not adjustments:
            return score
        
        adjusted_score = score
        
        # Apply context-specific boosts/reductions
        if "boost_negative" in adjustments and score < 0.5:
            adjusted_score = 0.5 - (0.5 - score) * adjustments["boost_negative"]
        
        if "reduce_positive" in adjustments and score > 0.5:
            adjusted_score = 0.5 + (score - 0.5) * adjustments["reduce_positive"]
        
        if "boost_positive" in adjustments and score > 0.5:
            adjusted_score = 0.5 + (score - 0.5) * adjustments["boost_positive"]
        
        if "boost_extremes" in adjustments:
            # Make extremes more extreme
            if score > 0.6 or score < 0.4:
                adjusted_score = 0.5 + (score - 0.5) * adjustments["boost_extremes"]
        
        return adjusted_score
    
    @staticmethod
    def detect_escalation_triggers(text: str) -> Tuple[bool, List[str]]:
        """
        Detect if text contains escalation triggers.
        
        Returns:
            Tuple of (is_escalation, trigger_list)
        """
        lower_text = text.lower()
        triggers_found = []
        
        for trigger_name, keywords in ESCALATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lower_text:
                    triggers_found.append(trigger_name)
                    break
        
        is_escalation = len(triggers_found) > 0
        return is_escalation, list(set(triggers_found))
    
    @staticmethod
    def get_sentiment_keywords(text: str) -> Dict[str, List[str]]:
        """
        Extract sentiment-bearing keywords from text.
        
        Returns:
            Dict with sentiment-related information
        """
        lower_text = text.lower()
        
        keywords = {
            "negations": [],
            "intensifiers": [],
            "diminishers": [],
            "escalators": [],
        }
        
        # Extract negations
        for neg in NEGATION_WORDS:
            if re.search(rf'\b{neg}\b', lower_text):
                keywords["negations"].append(neg)
        
        # Extract intensifiers
        for intens in INTENSIFIERS.keys():
            if re.search(rf'\b{intens}\b', lower_text):
                keywords["intensifiers"].append(intens)
        
        # Extract diminishers
        for dim in DIMINISHERS.keys():
            if re.search(rf'\b{dim}\b', lower_text):
                keywords["diminishers"].append(dim)
        
        # Extract escalation triggers
        for trigger_name, trigger_words in ESCALATION_KEYWORDS.items():
            for trigger in trigger_words:
                if re.search(rf'\b{trigger}\b', lower_text):
                    keywords["escalators"].append(trigger_name)
                    break
        
        return keywords


# Global rules engine instance
_rules_engine = SentimentRulesEngine()


def apply_sentiment_rules(
    score: float,
    text: str,
    context: Optional[str] = None
) -> float:
    """
    Convenience function to apply sentiment rules.
    
    Args:
        score: Initial sentiment score
        text: Original text
        context: Optional context
    
    Returns:
        Adjusted sentiment score
    """
    return _rules_engine.apply_rules(score, text, context)


def detect_escalation(text: str) -> Dict:
    """
    Check if text requires escalation.
    
    Returns:
        Dict with escalation info
    """
    is_escalation, triggers = _rules_engine.detect_escalation_triggers(text)
    keywords = _rules_engine.get_sentiment_keywords(text)
    
    return {
        "requires_escalation": is_escalation,
        "triggers": triggers,
        "keywords": keywords,
    }


def extract_sentiment_information(text: str) -> Dict:
    """
    Extract all sentiment-related information from text.
    
    Returns:
        Comprehensive sentiment information
    """
    keywords = _rules_engine.get_sentiment_keywords(text)
    is_escalation, triggers = _rules_engine.detect_escalation_triggers(text)
    
    return {
        "keywords": keywords,
        "escalation": {
            "required": is_escalation,
            "triggers": triggers,
        },
        "patterns": {
            "has_negation": len(keywords["negations"]) > 0,
            "has_intensity": len(keywords["intensifiers"]) > 0,
            "is_diminished": len(keywords["diminishers"]) > 0,
            "has_emphasis": bool(re.search(
                r"[A-Z]{3,}|!{2,}|\?{2,}",
                text
            )),
        },
    }
 
