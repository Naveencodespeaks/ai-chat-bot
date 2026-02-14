"""
Sentiment Analysis Module

Provides sentiment analysis capabilities for user messages using multiple strategies:
- Lexicon-based analysis
- Pattern-based rules
- Fallback mechanisms

Returns sentiment scores (0-1) and classifications (positive/negative/neutral)
"""

from typing import Dict, Optional, Tuple
from app.core.logging import logger
from app.sentiment.strategies import (
    lexicon_sentiment,
    pattern_sentiment,
)
from app.sentiment.rules import apply_sentiment_rules


class SentimentAnalyzer:
    """
    Enterprise-grade sentiment analyzer combining multiple strategies.
    
    Uses:
    1. Lexicon-based analysis (word scores)
    2. Pattern-based analysis (negations, intensifiers)
    3. Custom business rules (domain-specific adjustments)
    """
    
    def __init__(self):
        """Initialize the analyzer with strategies."""
        self.strategies = [
            ("lexicon", lexicon_sentiment),
            ("pattern", pattern_sentiment),
        ]
        logger.info("SentimentAnalyzer initialized")
    
    def analyze(self, text: str, context: Optional[str] = None) -> Dict:
        """
        Analyze sentiment of provided text.
        
        Args:
            text: Text to analyze
            context: Optional context (e.g., "customer_support", "product_review")
        
        Returns:
            Dictionary with:
            - score: float (0-1) where 0=negative, 0.5=neutral, 1=positive
            - label: str ("positive", "negative", "neutral")
            - confidence: float (0-1)
            - details: dict with individual strategy scores
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided to sentiment analyzer")
                return self._neutral_response()
            
            # Clean text
            cleaned_text = text.strip().lower()
            
            # Get scores from each strategy
            scores = {}
            for strategy_name, strategy_func in self.strategies:
                try:
                    score = strategy_func(cleaned_text)
                    scores[strategy_name] = score
                except Exception as e:
                    logger.error(f"Error in {strategy_name} strategy: {str(e)}")
                    scores[strategy_name] = 0.5  # Default to neutral
            
            # Combine scores (average)
            combined_score = sum(scores.values()) / len(scores) if scores else 0.5
            
            # Apply business rules
            final_score = apply_sentiment_rules(
                combined_score,
                cleaned_text,
                context=context
            )
            
            # Classify
            label = self._classify_sentiment(final_score)
            
            # Calculate confidence
            confidence = self._calculate_confidence(scores, final_score)
            
            result = {
                "score": round(final_score, 3),
                "label": label,
                "confidence": round(confidence, 3),
                "details": {
                    key: round(val, 3) for key, val in scores.items()
                },
                "combined_score": round(combined_score, 3),
            }
            
            logger.debug(
                f"Sentiment analyzed: score={final_score}, "
                f"label={label}, confidence={confidence}"
            )
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return self._neutral_response()
    
    def analyze_batch(
        self,
        texts: list,
        context: Optional[str] = None
    ) -> list:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of texts to analyze
            context: Optional context for all texts
        
        Returns:
            List of sentiment analysis results
        """
        try:
            results = []
            for text in texts:
                result = self.analyze(text, context)
                results.append(result)
            
            logger.info(f"Batch sentiment analysis completed: {len(texts)} texts")
            return results
        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {str(e)}")
            return [self._neutral_response() for _ in texts]
    
    def analyze_with_explanation(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        Analyze sentiment with detailed explanation.
        
        Args:
            text: Text to analyze
            context: Optional context
        
        Returns:
            Dict with sentiment analysis and explanation
        """
        result = self.analyze(text, context)
        
        try:
            # Identify key sentiment words
            sentiment_words = self._extract_sentiment_words(text)
            
            result["explanation"] = {
                "positive_words": sentiment_words.get("positive", []),
                "negative_words": sentiment_words.get("negative", []),
                "summary": self._generate_summary(result["label"], sentiment_words),
            }
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            result["explanation"] = None
        
        return result
    
    @staticmethod
    def _classify_sentiment(score: float) -> str:
        """
        Classify sentiment based on score.
        
        Score ranges:
        - 0.0 to 0.33: negative
        - 0.33 to 0.67: neutral
        - 0.67 to 1.0: positive
        """
        if score < 0.33:
            return "negative"
        elif score > 0.67:
            return "positive"
        else:
            return "neutral"
    
    @staticmethod
    def _calculate_confidence(scores: Dict[str, float], final_score: float) -> float:
        """
        Calculate confidence based on agreement between strategies.
        
        Higher confidence when all strategies agree on the direction.
        """
        if not scores:
            return 0.5
        
        # Check how many strategies agree with final classification
        final_label = SentimentAnalyzer._classify_sentiment(final_score)
        agreement_count = 0
        
        for score in scores.values():
            label = SentimentAnalyzer._classify_sentiment(score)
            if label == final_label:
                agreement_count += 1
        
        # Base confidence on agreement (0.5 to 1.0)
        base_confidence = 0.5 + (agreement_count / len(scores)) * 0.5
        
        # Adjust by distance from neutral (more extreme = more confident)
        distance_from_neutral = abs(final_score - 0.5) * 2  # 0 to 1
        
        confidence = (base_confidence + distance_from_neutral) / 2
        return min(confidence, 1.0)
    
    @staticmethod
    def _neutral_response() -> Dict:
        """Return neutral sentiment response."""
        return {
            "score": 0.5,
            "label": "neutral",
            "confidence": 0.0,
            "details": {},
            "combined_score": 0.5,
        }
    
    @staticmethod
    def _extract_sentiment_words(text: str) -> Dict[str, list]:
        """
        Extract sentiment-bearing words from text.
        
        Returns:
            Dict with lists of positive and negative words
        """
        from app.sentiment.strategies import POSITIVE_WORDS, NEGATIVE_WORDS
        
        words = text.lower().split()
        
        positive_found = [w for w in words if w in POSITIVE_WORDS]
        negative_found = [w for w in words if w in NEGATIVE_WORDS]
        
        return {
            "positive": list(set(positive_found)),
            "negative": list(set(negative_found)),
        }
    
    @staticmethod
    def _generate_summary(label: str, sentiment_words: Dict) -> str:
        """Generate human-readable summary of sentiment analysis."""
        pos_count = len(sentiment_words.get("positive", []))
        neg_count = len(sentiment_words.get("negative", []))
        
        if label == "positive":
            return f"Text contains {pos_count} positive indicators and {neg_count} negative indicators."
        elif label == "negative":
            return f"Text contains {pos_count} positive indicators and {neg_count} negative indicators."
        else:
            return f"Text sentiment is mixed or neutral with {pos_count} positive and {neg_count} negative words."


# Global analyzer instance
_analyzer = SentimentAnalyzer()


def analyze_sentiment(
    text: str,
    context: Optional[str] = None,
    detailed: bool = False
) -> Dict:
    """
    Convenience function for sentiment analysis.
    
    Args:
        text: Text to analyze
        context: Optional context
        detailed: If True, return detailed explanation
    
    Returns:
        Sentiment analysis result
    """
    if detailed:
        return _analyzer.analyze_with_explanation(text, context)
    return _analyzer.analyze(text, context)


def analyze_messages_sentiment(messages: list) -> list:
    """
    Analyze sentiment for a list of messages.
    
    Args:
        messages: List of message strings or dicts with 'content' key
    
    Returns:
        List of sentiment results
    """
    texts = []
    for msg in messages:
        if isinstance(msg, dict):
            texts.append(msg.get("content", ""))
        else:
            texts.append(str(msg))
    
    return _analyzer.analyze_batch(texts)
