"""Utility helpers for the AI communication assistant."""

import re
import io
import base64
import datetime as dt
from typing import List, Tuple

import pyttsx3
from googletrans import Translator


translator = Translator()


def pseudonymize(text: str) -> str:
    """Return a pseudonymised version of the text by replacing email addresses
    and phone numbers with placeholder tokens.
    """
    if not text:
        return text
    # Replace email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[email]', text)
    # Replace phone numbers (very basic pattern)
    text = re.sub(r'\b\+?\d[\d\s-]{7,}\b', '[phone]', text)
    return text


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract simple keywords by selecting unique words longer than 4
    characters.  This is a placeholder; for production use an NLP model.
    """
    words = re.findall(r'\b\w{5,}\b', text.lower())
    unique = list(dict.fromkeys(words))
    return unique[:max_keywords]


def calculate_priority(sentiment: str, urgency: bool, timestamp: dt.datetime) -> int:
    """Compute a priority score based on sentiment, urgency and message age."""
    score = 0
    if urgency:
        score += 50
    if sentiment == 'negative':
        score += 20
    elif sentiment == 'positive':
        score -= 10
    # Older messages become higher priority
    age_minutes = (dt.datetime.utcnow() - timestamp).total_seconds() / 60.0
    score += min(int(age_minutes / 10), 30)
    return max(score, 0)


def calculate_trust(confidence: float, heuristics_score: float = 0.0) -> float:
    """Combine the model's confidence with heuristic scoring into a single
    percentage value between 0 and 100."""
    # Weight AI confidence at 70% and heuristics at 30%
    trust = (confidence * 70.0) + (heuristics_score * 30.0)
    return max(0.0, min(trust, 100.0))


def translate_text(text: str, target_lang: str) -> str:
    """Translate text into the target language using googletrans.  If the
    translation fails or the target language is English, return the original
    text.
    """
    if not text or target_lang == 'en':
        return text
    try:
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception:
        return text


def text_to_speech(text: str, language: str = 'en') -> bytes:
    """Convert the given text to speech and return the audio as a WAV
    byte string.  Uses pyttsx3 which works offline.  In production you
    might store the file and stream it; here we return raw bytes.
    """
    engine = pyttsx3.init()
    # Attempt to set language; not all voices support Hindi
    try:
        for voice in engine.getProperty('voices'):
            if language in voice.languages[0].decode('utf-8').lower():
                engine.setProperty('voice', voice.id)
                break
    except Exception:
        pass
    with io.BytesIO() as buffer:
        engine.save_to_file(text, 'temp_audio.wav')
        engine.runAndWait()
        with open('temp_audio.wav', 'rb') as f:
            data = f.read()
        return data