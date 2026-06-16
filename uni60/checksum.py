"""
uni60/checksum.py
─────────────────────────────────────────────────────────────────────────────
HEXAGEN-60 Protocol — Luhn-60 Checksum Algorithm
Taylor Dynasty Systems | v1.0.0

Adapts the classic Luhn algorithm to Base-60, providing single-character
error detection for HEXAGEN-60 identifiers.

The Luhn-60 algorithm detects:
  · All single-character errors
  · All adjacent transpositions (swap of two neighbouring characters)

This is sufficient for typo detection in human-readable IDs.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations
from .core import ALPHABET, BASE, _CHAR_TO_VAL

__all__ = ["compute", "verify", "append"]


def compute(payload: str) -> str:
    """
    Compute the Luhn-60 check character for `payload`.

    Args:
        payload: Base-60 string (without checksum).

    Returns:
        Single Base-60 character (the check digit).

    Raises:
        ValueError: If payload contains invalid characters.
    """
    total = 0
    for i, char in enumerate(reversed(payload)):
        if char not in _CHAR_TO_VAL:
            raise ValueError(f"Invalid character '{char}' in payload")
        value = _CHAR_TO_VAL[char]
        if i % 2 == 0:                  # Double every second digit from the right
            value *= 2
            if value >= BASE:
                value = (value % BASE) + (value // BASE)
        total += value

    check_value = (BASE - (total % BASE)) % BASE
    return ALPHABET[check_value]


def verify(encoded: str) -> bool:
    """
    Verify that `encoded` has a valid Luhn-60 check character (last character).

    Args:
        encoded: Full Base-60 string including the check character.

    Returns:
        True if checksum is valid, False otherwise.

    Examples:
        >>> encoded = append("B4xq")
        >>> verify(encoded)
        True
        >>> verify(encoded[:-1] + "0")   # Corrupt the checksum
        False
    """
    if len(encoded) < 2:
        return False
    payload, check = encoded[:-1], encoded[-1]
    return compute(payload) == check


def append(payload: str) -> str:
    """
    Append a Luhn-60 check character to `payload`.

    Args:
        payload: Base-60 string (without checksum).

    Returns:
        payload + check character.

    Examples:
        >>> append("B4xq")
        'B4xqC'
    """
    return payload + compute(payload)
