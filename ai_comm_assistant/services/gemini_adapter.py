"""Adapter layer encapsulating interactions with Google Gemini APIs.

This module provides convenience wrappers for both text and vision models.
It accepts plain text, images, PDFs and audio files and performs the
appropriate conversion before sending requests to the Google Gemini API.
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
from dataclasses import dataclass
from typing import List, Tuple

import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_path
import pytesseract

from ..config import Config
from ..utils import extract_keywords
import whisper


class GeminiAdapter:
    """A thin wrapper around the Google Gemini API for both text and vision."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or Config.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY is not configured')
        genai.configure(api_key=api_key)
        # Create model instances
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        # Load whisper model lazily
        self._whisper_model = None

    @property
    def whisper_model(self):
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model('base')
        return self._whisper_model

    def generate_reply(self, thread_text: str, kb_context: str, tone: str,
                       sentiment: str, urgency: bool) -> dict:
        """Generate a reply given the thread text, knowledge context and tone.

        Returns a dict with keys: reply_text, justification, confidence.
        """
        prompt = (
            "You are an empathetic AI email assistant. Given the email thread, context, "
            "sentiment, urgency and tone, generate a professional, empathetic reply. "
            "Also provide a short justification explaining why this reply is appropriate.\n\n"
            f"Thread:\n{thread_text}\n\n"
            f"Context:\n{kb_context}\n\n"
            f"Sentiment: {sentiment}\nUrgency: {urgency}\nTone: {tone}\n\n"
            "Reply:" )
        try:
            response = self.text_model.generate_content(prompt, safety_settings={})
            text = response.text if hasattr(response, 'text') else str(response)
            # Heuristic confidence: if model returns candidate_scores
            confidence = getattr(response, 'candidate_info', {}).get('probability', 0.6)
            # Attempt to split justification
            parts = text.split('Justification:')
            reply_text = parts[0].strip()
            justification = parts[1].strip() if len(parts) > 1 else ''
            return {
                'reply_text': reply_text,
                'justification': justification,
                'confidence': float(confidence),
            }
        except Exception as e:
            # Fallback: return a generic message
            return {
                'reply_text': 'I am sorry, I could not generate a reply due to an internal error.',
                'justification': f'Gemini API error: {e}',
                'confidence': 0.0,
            }

    def _encode_image(self, image: Image.Image) -> Tuple[str, str]:
        """Encode an image into base64 and return (mime_type, data)."""
        buffered = io.BytesIO()
        image.save(buffered, format='PNG')
        b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return 'image/png', b64

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from an image, PDF or audio file using Gemini Vision and Whisper.

        This function handles the following:
        * Images (png, jpg, jpeg, bmp, gif) → Gemini Vision (OCR)
        * PDFs → convert each page to an image, run through Gemini Vision
        * Audio (wav, mp3, m4a, flac) → Whisper transcription
        * Fallback for other types → pytesseract OCR
        """
        if not os.path.exists(file_path):
            return ''
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if ext in {'png', 'jpg', 'jpeg', 'bmp', 'gif'}:
            return self._extract_text_from_images([Image.open(file_path)])
        elif ext == 'pdf':
            try:
                pages = convert_from_path(file_path)
                return self._extract_text_from_images(pages)
            except Exception:
                # Fallback to tesseract on rasterised pages
                pages = convert_from_path(file_path, dpi=200)
                return self._extract_text_from_images(pages)
        elif ext in {'wav', 'mp3', 'm4a', 'flac', 'ogg'}:
            return self._transcribe_audio(file_path)
        else:
            # Generic image OCR
            return pytesseract.image_to_string(Image.open(file_path))

    def _extract_text_from_images(self, images: List[Image.Image]) -> str:
        """Send one or more images to Gemini Vision and return concatenated text."""
        contents = []
        for img in images:
            mime, data = self._encode_image(img)
            contents.append({"image": {"data": data, "mime_type": mime}})
        # Add an instruction to summarise text from images
        contents.append({"text": "Please extract and return all visible text in the provided images."})
        try:
            response = self.vision_model.generate_content(contents)
            return response.text
        except Exception:
            # Fallback to pytesseract
            text = ''
            for img in images:
                text += pytesseract.image_to_string(img)
            return text

    def _transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio using the Whisper model."""
        try:
            result = self.whisper_model.transcribe(file_path)
            return result.get('text', '')
        except Exception:
            return ''