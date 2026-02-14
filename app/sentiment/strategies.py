"""
Sentiment Analysis Strategies

Implements multiple strategies for sentiment analysis:
1. Lexicon-based: Uses sentiment word dictionaries
2. Pattern-based: Uses linguistic patterns and context
3. Statistical: Uses word frequency and distribution

Each strategy operates independently and returns a 0-1 sentiment score.
"""

import re
from typing import Dict, List, Tuple, Optional
from app.core.logging import logger


# -------------------------------------------------
# POSITIVE SENTIMENT WORDS
# -------------------------------------------------
POSITIVE_WORDS = {
    # Emotions
    "happy", "joy", "joyful", "glad", "delighted", "pleased",
    "excited", "thrilled", "ecstatic", "wonderful", "fantastic",
    "excellent", "amazing", "awesome", "great", "good", "nice",
    "beautiful", "lovely", "charming", "pleasant", "delightful",
    "satisfied", "content", "cheerful", "upbeat", "optimistic",
    
    # Appreciation
    "love", "adore", "appreciate", "grateful", "thankful", "blessed",
    "honored", "proud", "confident", "brave", "strong", "powerful",
    
    # Quality
    "perfect", "superb", "outstanding", "magnificent", "brilliant",
    "stellar", "tremendous", "remarkable", "impressive", "noteworthy",
    "creative", "innovative", "intelligent", "smart", "clever",
    
    # Success
    "success", "win", "won", "achieved", "accomplished", "completed",
    "solved", "fixed", "improved", "enhanced", "upgraded", "better",
    "excellent", "superior", "premium", "quality", "professional",
    
    # Agreement
    "agree", "yes", "okay", "alright", "sure", "absolutely", "definitely",
    "certainly", "indeed", "true", "correct", "right", "perfect",
    
    # Recommendations
    "recommend", "suggest", "advise", "best", "ideal", "suitable",
    "appropriate", "worthy", "deserving", "justified", "reasonable",
}

# -------------------------------------------------
# NEGATIVE SENTIMENT WORDS
# -------------------------------------------------
NEGATIVE_WORDS = {
    # Emotions
    "sad", "unhappy", "depressed", "miserable", "despair", "hopeless",
    "angry", "furious", "enraged", "outraged", "livid", "mad",
    "frustrated", "irritated", "annoyed", "bothered", "upset",
    "disappointed", "let down", "discouraged", "disheartened",
    "anxious", "worried", "nervous", "scared", "afraid", "terrified",
    "confused", "bewildered", "puzzled", "perplexed",
    
    # Criticism
    "bad", "terrible", "awful", "horrible", "dreadful", "atrocious",
    "disgusting", "repulsive", "revolting", "nasty", "vile", "ugly",
    "mediocre", "poor", "subpar", "inferior", "weak", "useless",
    "worthless", "ineffective", "inefficient", "broken", "buggy",
    
    # Problems
    "problem", "issue", "defect", "fault", "error", "bug", "glitch",
    "crash", "fail", "failed", "failure", "mistake", "wrong", "broken",
    "damage", "damaged", "destroy", "destroyed", "harm", "hurt",
    
    # Complaints
    "complain", "complaint", "gripe", "whine", "moan", "rant",
    "hate", "despise", "detest", "abhor", "loathe", "dislike",
    "avoid", "refuse", "reject", "dismiss", "ignore",
    
    # Negation
    "no", "not", "never", "neither", "none", "nothing",
    "nobody", "nowhere", "useless", "pointless", "worthless",
    
    # Disagreement
    "disagree", "wrong", "incorrect", "false", "misleading", "deceptive",
    "fraudulent", "dishonest", "unfair", "unjust", "unreasonable",
    
    # Financial
    "expensive", "overpriced", "costly", "waste", "scam", "fraud",
    "refund", "charge", "cancel", "return", "complaint", "sue",
}

# -------------------------------------------------
# NEUTRAL/WEAK SENTIMENT WORDS
# -------------------------------------------------
NEUTRAL_WORDS = {
    "okay", "fine", "alright", "normal", "average", "regular",
    "common", "usual", "typical", "standard", "basic", "simple",
    "interesting", "notable", "significant", "important", "relevant",
}

# -------------------------------------------------
# EMOTICON/EMOJI PATTERNS
# -------------------------------------------------
EMOTICON_PATTERNS = {
    "positive": [
        r":\)|:-\)|:D|:-D|\(",  # :) :D etc
        r";\)|;-\)|;\(|;D",     # ;) winky
        r"\^_\^|\^\^",           # ^_^
        r"😊|😃|😄|😁|😆|😂|🤣|😍|😘|👍|🎉|🎊",  # emoji
    ],
    "negative": [
        r":\(|:-\(|:'\(|:\[",   # :( sad
        r":|:-|>:\(|>:-\(",      # >:( angry
        r":@|:-@",               # :@ angry
        r"😢|😭|😞|😠|😡|👎|💔|😤|🤬",  # emoji
    ],
}

# -------------------------------------------------
# NEGATION AND MODIFIER CONTEXT WINDOW
# -------------------------------------------------
CONTEXT_WINDOW = 3  # Words before/after to consider


class LexiconStrategy:
    """
    Lexicon-based sentiment analysis.
    
    Uses pre-built dictionaries of sentiment words to score text.
    """
    
    def __init__(self):
        """Initialize lexicon strategy."""
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.neutral_words = NEUTRAL_WORDS
        logger.info("LexiconStrategy initialized")
    
    def analyze(self, text: str) -> float:
        """
        Analyze sentiment using lexicon.
        
        Args:
            text: Text to analyze
        
        Returns:
            Sentiment score (0-1)
        """
        try:
            words = text.lower().split()
            
            if not words:
                return 0.5
            
            positive_count = 0
            negative_count = 0
            
            # Count sentiment words
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                
                if clean_word in self.positive_words:
                    positive_count += 1
                elif clean_word in self.negative_words:
                    negative_count += 1
            
            total_sentiment_words = positive_count + negative_count
            
            if total_sentiment_words == 0:
                return 0.5  # Neutral
            
            # Calculate score: positive/(positive+negative)
            score = positive_count / total_sentiment_words
            
            return score
        except Exception as e:
            logger.error(f"Error in lexicon strategy: {str(e)}")
            return 0.5


class PatternStrategy:
    """
    Pattern-based sentiment analysis.
    
    Uses linguistic patterns, emoticons, and context to score sentiment.
    """
    
    def __init__(self):
        """Initialize pattern strategy."""
        logger.info("PatternStrategy initialized")
    
    def analyze(self, text: str) -> float:
        """
        Analyze sentiment using patterns.
        
        Args:
            text: Text to analyze
        
        Returns:
            Sentiment score (0-1)
        """
        try:
            score = 0.5  # Start neutral
            
            # Check for emoticons
            emoticon_score = self._check_emoticons(text)
            if emoticon_score is not None:
                score = emoticon_score
            
            # Check for exclamations/questions
            exclamation_score = self._check_punctuation(text)
            if exclamation_score is not None:
                # Blend with existing score
                score = (score + exclamation_score) / 2
            
            # Check for emphasis patterns
            emphasis_score = self._check_emphasis(text)
            if emphasis_score is not None:
                score = (score + emphasis_score) / 2
            
            return score
        except Exception as e:
            logger.error(f"Error in pattern strategy: {str(e)}")
            return 0.5
    
    @staticmethod
    def _check_emoticons(text: str) -> Optional[float]:
        """Check for emoticons/emojis."""
        # Check positive emoticons
        for pattern in EMOTICON_PATTERNS["positive"]:
            if re.search(pattern, text):
                return 0.8
        
        # Check negative emoticons
        for pattern in EMOTICON_PATTERNS["negative"]:
            if re.search(pattern, text):
                return 0.2
        
        return None
    
    @staticmethod
    def _check_punctuation(text: str) -> Optional[float]:
        """
        Check punctuation patterns.
        
        Returns:
            Sentiment adjustment based on punctuation
        """
        # Count punctuation
        exclamation_count = len(re.findall(r'!', text))
        question_count = len(re.findall(r'\?', text))
        
        # Multiple exclamations suggest strong positive (context-dependent)
        if exclamation_count > 2:
            return 0.7
        
        # Multiple questions suggest uncertainty/confusion (slightly negative)
        if question_count > 2:
            return 0.4
        
        # Single exclamation is mildly positive
        if exclamation_count == 1:
            return 0.6
        
        return None
    
    @staticmethod
    def _check_emphasis(text: str) -> Optional[float]:
        """
        Check emphasis patterns (caps, repeats).
        
        Returns:
            Sentiment adjustment based on emphasis
        """
        # Check for ALL CAPS (often negative in online text)
        caps_ratio = len(re.findall(r'[A-Z]', text)) / (len(text) + 1)
        if caps_ratio > 0.5:
            return 0.3  # Likely angry/negative
        
        # Check for repeated characters (zzzz, !!!!)
        if re.search(r'(.)\1{3,}', text):
            return 0.6  # Emphasis, usually positive
        
        return None


class StatisticalStrategy:
    """
    Statistical sentiment analysis.
    
    Uses word frequency and distribution patterns.
    """
    
    def __init__(self):
        """Initialize statistical strategy."""
        logger.info("StatisticalStrategy initialized")
    
    def analyze(self, text: str) -> float:
        """
        Analyze sentiment using statistical measures.
        
        Args:
            text: Text to analyze
        
        Returns:
            Sentiment score (0-1)
        """
        try:
            words = text.lower().split()
            
            if not words:
                return 0.5
            
            # Calculate average word sentiment
            word_scores = []
            
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                score = self._get_word_sentiment(clean_word)
                word_scores.append(score)
            
            if not word_scores:
                return 0.5
            
            # Average sentiment
            average_sentiment = sum(word_scores) / len(word_scores)
            
            # Apply text length factor
            # Longer texts with consistent sentiment are more confident
            length_factor = min(len(words) / 30, 1.0)  # Normalize to 30 words
            
            # Blend average with neutral based on length confidence
            final_score = 0.5 + (average_sentiment - 0.5) * length_factor
            
            return final_score
        except Exception as e:
            logger.error(f"Error in statistical strategy: {str(e)}")
            return 0.5
    
    @staticmethod
    def _get_word_sentiment(word: str) -> float:
        """Get sentiment score for a single word."""
        if word in POSITIVE_WORDS:
            return 0.75
        elif word in NEGATIVE_WORDS:
            return 0.25
        elif word in NEUTRAL_WORDS:
            return 0.5
        else:
            return 0.5  # Default neutral


# -------------------------------------------------
# STRATEGY INSTANCES
# -------------------------------------------------
_lexicon_strategy = LexiconStrategy()
_pattern_strategy = PatternStrategy()
_statistical_strategy = StatisticalStrategy()


# -------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------


def lexicon_sentiment(text: str) -> float:
    """
    Analyze sentiment using lexicon strategy.
    
    Args:
        text: Text to analyze
    
    Returns:
        Sentiment score (0-1)
    """
    return _lexicon_strategy.analyze(text)


def pattern_sentiment(text: str) -> float:
    """
    Analyze sentiment using pattern strategy.
    
    Args:
        text: Text to analyze
    
    Returns:
        Sentiment score (0-1)
    """
    return _pattern_strategy.analyze(text)


def statistical_sentiment(text: str) -> float:
    """
    Analyze sentiment using statistical strategy.
    
    Args:
        text: Text to analyze
    
    Returns:
        Sentiment score (0-1)
    """
    return _statistical_strategy.analyze(text)


def hybrid_sentiment(text: str, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Analyze sentiment using weighted hybrid of all strategies.
    
    Args:
        text: Text to analyze
        weights: Dict with weights for each strategy
                Default: {"lexicon": 0.5, "pattern": 0.3, "statistical": 0.2}
    
    Returns:
        Sentiment score (0-1)
    """
    if weights is None:
        weights = {
            "lexicon": 0.5,
            "pattern": 0.3,
            "statistical": 0.2,
        }
    
    try:
        lexicon_score = lexicon_sentiment(text)
        pattern_score = pattern_sentiment(text)
        statistical_score = statistical_sentiment(text)
        
        # Normalize weights
        total_weight = sum(weights.values())
        
        hybrid_score = (
            lexicon_score * (weights.get("lexicon", 0) / total_weight) +
            pattern_score * (weights.get("pattern", 0) / total_weight) +
            statistical_score * (weights.get("statistical", 0) / total_weight)
        )
        
        return hybrid_score
    except Exception as e:
        logger.error(f"Error in hybrid sentiment: {str(e)}")
        return 0.5


def analyze_with_confidence(
    text: str,
    strategy: str = "hybrid"
) -> Dict[str, float]:
    """
    Analyze sentiment with confidence score.
    
    Args:
        text: Text to analyze
        strategy: Strategy to use (lexicon, pattern, statistical, hybrid)
    
    Returns:
        Dict with score and confidence
    """
    try:
        scores = {
            "lexicon": lexicon_sentiment(text),
            "pattern": pattern_sentiment(text),
            "statistical": statistical_sentiment(text),
        }
        
        if strategy == "hybrid":
            main_score = hybrid_sentiment(text)
        else:
            main_score = scores.get(strategy, 0.5)
        
        # Calculate confidence based on agreement between strategies
        score_variance = (
            (scores["lexicon"] - main_score) ** 2 +
            (scores["pattern"] - main_score) ** 2 +
            (scores["statistical"] - main_score) ** 2
        ) / 3
        
        confidence = 1.0 - min(score_variance, 1.0)
        
        return {
            "score": main_score,
            "confidence": confidence,
            "strategy_scores": scores,
        }
    except Exception as e:
        logger.error(f"Error in analyze_with_confidence: {str(e)}")
        return {
            "score": 0.5,
            "confidence": 0.0,
            "strategy_scores": {},
        }


def get_sentiment_components(text: str) -> Dict:
    """
    Get detailed sentiment components.
    
    Returns:
        Dict with detailed sentiment breakdown
    """
    try:
        words = text.lower().split()
        
        positive_words = [
            w for w in words
            if re.sub(r'[^\w]', '', w) in POSITIVE_WORDS
        ]
        negative_words = [
            w for w in words
            if re.sub(r'[^\w]', '', w) in NEGATIVE_WORDS
        ]
        
        return {
            "total_words": len(words),
            "positive_words": positive_words,
            "negative_words": negative_words,
            "positive_ratio": len(positive_words) / (len(words) + 1),
            "negative_ratio": len(negative_words) / (len(words) + 1),
            "sentiment_word_count": len(positive_words) + len(negative_words),
        }
    except Exception as e:
        logger.error(f"Error in get_sentiment_components: {str(e)}")
        return {
            "total_words": 0,
            "positive_words": [],
            "negative_words": [],
            "positive_ratio": 0,
            "negative_ratio": 0,
            "sentiment_word_count": 0,
        }
