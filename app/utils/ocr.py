"""
OCR and text extraction utilities.
"""

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image using OCR.
    """
    return pytesseract.image_to_string(Image.open(file_path))
