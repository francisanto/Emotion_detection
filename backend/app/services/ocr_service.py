"""OCR service for extracting chat messages from screenshots."""

from __future__ import annotations

import re
from typing import Dict, List

import cv2
import pytesseract

from app.core.logging import get_logger
from app.utils.image_processing import preprocess_for_ocr

logger = get_logger("ocr_service")


SENDER_MESSAGE_PATTERNS = [
    # e.g., "Adith: Hey how are you?"
    re.compile(r"^(?P<sender>[A-Z][A-Za-z0-9_ ]{0,30})[:\-]\s+(?P<text>.+)$"),
    # e.g., "Adith Hey how are you?" (space-separated, first token is sender)
    re.compile(r"^(?P<sender>[A-Z][A-Za-z0-9_]{1,20})\s+(?P<text>.+)$"),
]


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


def extract_chat_text(image_path: str) -> List[Dict]:
    """
    Extract structured chat messages from a screenshot.

    Steps:
      1. Load + preprocess image (grayscale, denoise, threshold)
      2. Run Tesseract OCR
      3. Parse into list of {sender, text} dicts
    """
    logger.info("Starting OCR for chat screenshot", extra={"image_path": image_path})

    # Preprocess image
    _, binary = preprocess_for_ocr(image_path)

    # Optional: enlarge for better OCR on small fonts
    h, w = binary.shape[:2]
    if min(h, w) < 700:
        scale = 2.0
        binary = cv2.resize(binary, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

    # Tesseract config optimized for text lines
    config = "--oem 3 --psm 6"
    ocr_text = pytesseract.image_to_string(binary, config=config)

    lines = [ln for ln in ocr_text.splitlines() if ln.strip()]
    messages = _parse_chat_lines(lines)

    logger.info(
        "OCR completed",
        extra={"image_path": image_path, "raw_line_count": len(lines), "message_count": len(messages)},
    )
    return messages

