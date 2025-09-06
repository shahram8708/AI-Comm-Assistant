"""Tests for Gemini adapter.

These tests do not hit the real API; instead they check that the adapter
gracefully handles missing or invalid API keys.
"""

import os

from ai_comm_assistant.services.gemini_adapter import GeminiAdapter


def test_generate_reply_fallback(monkeypatch):
    # Set invalid API key to trigger fallback
    os.environ['GEMINI_API_KEY'] = 'invalid'
    adapter = GeminiAdapter()
    result = adapter.generate_reply('Hello', '', 'formal', 'neutral', False)
    assert 'reply_text' in result
    # With invalid key the confidence should be low (0.0)
    assert result['confidence'] <= 0.6