"""Basic sentiment and urgency detection heuristics."""

import re
from typing import Tuple


NEGATIVE_KEYWORDS = {'complain', 'terrible', 'bad', 'angry', 'frustrated', 'upset', 'issue', 'problem', 'unhappy', 'unsatisfied'}
POSITIVE_KEYWORDS = {'thank', 'great', 'good', 'appreciate', 'love', 'happy', 'excellent'}
URGENCY_KEYWORDS = {'urgent', 'immediately', 'asap', 'as soon as possible', 'now', 'important'}


def detect_sentiment_and_urgency(text: str) -> Tuple[str, bool]:
    """Return a tuple of (sentiment, urgency) based on simple keyword heuristics."""
    if not text:
        return 'neutral', False
    lowered = text.lower()
    sentiment = 'neutral'
    positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in lowered)
    negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in lowered)
    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    urgency = any(kw in lowered for kw in URGENCY_KEYWORDS)
    return sentiment, urgency