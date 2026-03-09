"""Audio feature extraction using librosa."""

from pathlib import Path
from typing import Any

import numpy as np


def extract_mfcc(
    audio_path: str | Path,
    *,
    sr: int = 22050,
    n_mfcc: int = 13,
    n_fft: int = 2048,
    hop_length: int = 512,
) -> list[list[float]]:
    """
    Extract MFCC features from audio file using librosa.

    Args:
        audio_path: Path to audio file (wav, mp3, etc.)
        sr: Target sample rate.
        n_mfcc: Number of MFCC coefficients.
        n_fft: FFT window size.
        hop_length: Hop length for framing.

    Returns:
        MFCC matrix as list of lists (n_mfcc x n_frames).
    """
    import librosa

    y, _ = librosa.load(str(audio_path), sr=sr, mono=True)
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )
    return mfcc.tolist()


def extract_mfcc_from_bytes(
    audio_bytes: bytes,
    *,
    sr: int = 22050,
    n_mfcc: int = 13,
    n_fft: int = 2048,
    hop_length: int = 512,
) -> list[list[float]]:
    """
    Extract MFCC from raw audio bytes (e.g., uploaded file).

    Args:
        audio_bytes: Raw audio bytes.
        sr: Target sample rate.
        n_mfcc: Number of MFCC coefficients.
        n_fft: FFT window size.
        hop_length: Hop length.

    Returns:
        MFCC matrix as list of lists.
    """
    import io

    import librosa
    import soundfile as sf

    buffer = io.BytesIO(audio_bytes)
    y, file_sr = sf.read(buffer)
    if len(y.shape) > 1:
        y = y.mean(axis=1)
    if file_sr != sr:
        y = librosa.resample(y.astype(float), orig_sr=file_sr, target_sr=sr)
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )
    return mfcc.tolist()


def mfcc_to_flat_features(mfcc_matrix: list[list[float]]) -> list[float]:
    """Convert MFCC matrix to flat feature vector (mean per coefficient)."""
    arr = np.array(mfcc_matrix)
    return np.mean(arr, axis=1).tolist()
