"""Text preprocessing utilities."""

import re
import string
from typing import Any


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace into single space."""
    return " ".join(text.split())


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    url_pattern = re.compile(
        r"https?://\S+|www\.\S+|ftp://\S+",
        re.IGNORECASE,
    )
    return url_pattern.sub("", text)


def remove_extra_punctuation(text: str) -> str:
    """Reduce repeated punctuation (e.g., !!! -> !)."""
    return re.sub(r"([.!?]){2,}", r"\1", text)


def preprocess_text(text: str) -> str:
    """
    Preprocess input text for emotion/intent analysis.

    Args:
        text: Raw input text.

    Returns:
        Cleaned and normalized text.
    """
    if not text or not isinstance(text, str):
        return ""

    t = text.strip().lower()
    t = remove_urls(t)
    t = normalize_whitespace(t)
    t = remove_extra_punctuation(t)
    return t


def extract_simple_features(text: str) -> dict[str, Any]:
    """
    Extract basic features from text for placeholder model.

    Real implementations would use embeddings (e.g., sentence-transformers).
    """
    cleaned = preprocess_text(text)
    words = cleaned.split()

    return {
        "word_count": len(words),
        "char_count": len(cleaned),
        "has_question": "?" in text,
        "has_exclamation": "!" in text,
        "exclamation_count": text.count("!"),
    }
