"""Image preprocessing utilities for OCR on chat screenshots."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


def load_image_bgr(path: str) -> np.ndarray:
    """Load an image from disk in BGR format."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at path: {path}")
    return img


def to_grayscale(img_bgr: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def denoise_image(gray: np.ndarray) -> np.ndarray:
    """Apply light denoising suitable for text regions."""
    # Bilateral filter preserves edges better than Gaussian blur
    return cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """
    Adaptive thresholding for robust binarization in noisy / uneven lighting.
    """
    return cv2.adaptiveThreshold(
        gray,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY_INV,
        blockSize=31,
        C=15,
    )


def preprocess_for_ocr(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Full preprocessing pipeline for OCR:
      1. Load
      2. Grayscale
      3. Denoise
      4. Adaptive threshold

    Returns:
        (original_bgr, binary_image)
    """
    bgr = load_image_bgr(path)
    gray = to_grayscale(bgr)
    denoised = denoise_image(gray)
    binary = adaptive_threshold(denoised)
    return bgr, binary

