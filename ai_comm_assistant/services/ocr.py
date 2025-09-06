"""Simple OCR utilities built on top of Tesseract and pdf2image."""

import os
from typing import List

import pytesseract
from PIL import Image
from pdf2image import convert_from_path


def ocr_image(file_path: str) -> str:
    """Extract text from an image using Tesseract."""
    if not os.path.exists(file_path):
        return ''
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except Exception:
        return ''


def pdf_to_text(file_path: str) -> str:
    """Convert a PDF to images and extract text from each page."""
    text = ''
    if not os.path.exists(file_path):
        return text
    try:
        pages = convert_from_path(file_path)
    except Exception:
        pages = convert_from_path(file_path, dpi=200)
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text