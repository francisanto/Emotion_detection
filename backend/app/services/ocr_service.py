"""OCR service for extracting chat messages from screenshots."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import cv2
import pytesseract

from app.core.logging import get_logger
from app.utils.image_processing import preprocess_for_ocr

logger = get_logger("ocr_service")
_easyocr_reader = None


SENDER_MESSAGE_PATTERNS = [
    # e.g., "Adith: Hey how are you?"
    re.compile(r"^(?P<sender>[A-Z][A-Za-z0-9_ ]{0,30})[:\-]\s+(?P<text>.+)$"),
    # e.g., "Adith Hey how are you?" (space-separated, first token is sender)
    re.compile(r"^(?P<sender>[A-Z][A-Za-z0-9_]{1,20})\s+(?P<text>.+)$"),
]


def _configure_tesseract() -> None:
    """
    Try to auto-configure tesseract path on Windows to avoid OCR runtime failures.
    """
    candidates = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    for exe in candidates:
        if exe.exists():
            pytesseract.pytesseract.tesseract_cmd = str(exe)
            return


def _get_easyocr_reader():
    """
    Lazy-load EasyOCR reader.

    EasyOCR downloads required OCR weights automatically on first run.
    """
    global _easyocr_reader
    if _easyocr_reader is not None:
        return _easyocr_reader
    try:
        import easyocr

        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("EasyOCR reader initialized")
    except Exception as exc:
        logger.warning("EasyOCR unavailable; fallback to Tesseract only", extra={"error": str(exc)})
        _easyocr_reader = False
    return _easyocr_reader


def _clean_ocr_line(line: str) -> str:
    line = line.strip()
    # Remove stray non-printable characters
    line = re.sub(r"[^\x20-\x7E]+", " ", line)
    return line.strip()


def _parse_chat_lines(lines: List[str]) -> List[Dict]:
    """
    Parse OCR-extracted lines into structured chat messages using simple heuristics.
    """
    messages: List[Dict] = []

    for raw_line in lines:
        line = _clean_ocr_line(raw_line)
        if not line:
            continue

        matched = False
        for pattern in SENDER_MESSAGE_PATTERNS:
            m = pattern.match(line)
            if m:
                sender = m.group("sender").strip()
                text = m.group("text").strip()
                if text:
                    messages.append({"sender": sender, "text": text})
                    matched = True
                    break

        if not matched:
            # Continuation of previous message, if any
            if messages:
                messages[-1]["text"] = (messages[-1]["text"] + " " + line).strip()

    return messages


def _fallback_messages_from_lines(lines: List[str]) -> List[Dict]:
    """
    Fallback parser for screenshots where sender/text structure is unclear.
    """
    messages: List[Dict] = []
    for raw_line in lines:
        line = _clean_ocr_line(raw_line)
        if not line:
            continue
        if len(line) < 2:
            continue
        # Skip likely timestamps like 10:45 PM or 22:10
        if re.match(r"^\d{1,2}[:.]\d{2}(\s?[APMapm]{2})?$", line):
            continue
        messages.append({"sender": "Unknown", "text": line})
    return messages


def extract_chat_text(image_path: str) -> List[Dict]:
    """
    Extract structured chat messages from a screenshot.

    Steps:
      1. Load + preprocess image (grayscale, denoise, threshold)
      2. Run Tesseract OCR
      3. Parse into list of {sender, text} dicts
    """
    logger.info("Starting OCR for chat screenshot", extra={"image_path": image_path})
    _configure_tesseract()

    # Preprocess image
    original_bgr, binary = preprocess_for_ocr(image_path)

    # Optional: enlarge for better OCR on small fonts
    h, w = binary.shape[:2]
    if min(h, w) < 700:
        scale = 2.0
        binary = cv2.resize(binary, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

    # Tesseract config optimized for text lines
    config = "--oem 3 --psm 6"
    try:
        ocr_text = pytesseract.image_to_string(binary, config=config)
    except Exception as exc:
        logger.exception("OCR execution failed", extra={"error": str(exc)})
        return []

    lines = [ln for ln in ocr_text.splitlines() if ln.strip()]
    messages = _parse_chat_lines(lines)
    if not messages:
        # Second OCR pass on original image for complex chat backgrounds.
        retry_text = pytesseract.image_to_string(original_bgr, config="--oem 3 --psm 11")
        retry_lines = [ln for ln in retry_text.splitlines() if ln.strip()]
        messages = _parse_chat_lines(retry_lines)
        if not messages:
            messages = _fallback_messages_from_lines(retry_lines)
    if not messages:
        messages = _fallback_messages_from_lines(lines)

    if not messages:
        # Final fallback using EasyOCR (better for stylized screenshots).
        reader = _get_easyocr_reader()
        if reader:
            try:
                easy_results = reader.readtext(image_path, detail=0)
                easy_lines = [str(x) for x in easy_results if str(x).strip()]
                messages = _parse_chat_lines(easy_lines)
                if not messages:
                    messages = _fallback_messages_from_lines(easy_lines)
            except Exception as exc:
                logger.warning("EasyOCR extraction failed", extra={"error": str(exc)})

    logger.info(
        "OCR completed",
        extra={"image_path": image_path, "raw_line_count": len(lines), "message_count": len(messages)},
    )
    return messages

