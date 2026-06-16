"""
uni60/core.py
─────────────────────────────────────────────────────────────────────────────
HEXAGEN-60 Protocol — Core Base-60 Encoding Engine
Taylor Dynasty Systems | v1.0.0

The HEXAGEN-60 alphabet uses 60 carefully selected characters:
  · Digits 0–9     (10 chars)
  · Uppercase A–Z  (24 chars, excluding I and O — visually ambiguous)
  · Lowercase a–z  (24 chars, excluding l and o — visually ambiguous)
  · Extended ★☆    (2 Unicode symbols, U+2605 and U+2606)

This gives us exactly 60 unambiguous, URL-safe*, human-readable symbols.
(*Extended symbols require percent-encoding in URLs; use encode_url() for safe URLs)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

__all__ = [
    "ALPHABET",
    "BASE",
    "encode",
    "decode",
    "encode_url",
    "decode_url",
    "is_valid",
    "pad",
]

# ── Symbol Set ────────────────────────────────────────────────────────────────

_DIGITS    = "0123456789"                         # 10 symbols  (0–9)
_UPPER     = "ABCDEFGHJKLMNPQRSTUVWXYZ"           # 24 symbols  (10–33)  — no I, O
_LOWER     = "abcdefghijkmnpqrstuvwxyz"           # 24 symbols  (34–57)  — no l, o
_EXTENDED  = "\u2605\u2606"                       #  2 symbols  (58–59)  — ★ ☆

ALPHABET: str = _DIGITS + _UPPER + _LOWER + _EXTENDED
BASE: int     = len(ALPHABET)   # Must be exactly 60

assert BASE == 60, f"ALPHABET length must be 60, got {BASE}"

# Reverse lookup: char → value
_CHAR_TO_VAL: dict[str, int] = {ch: i for i, ch in enumerate(ALPHABET)}

# URL-safe fallback (no Unicode): replace ★→"$" ☆→"_"
_URL_SAFE_ALPHABET: str = ALPHABET[:58] + "$_"
_URL_CHAR_TO_VAL:   dict[str, int] = {ch: i for i, ch in enumerate(_URL_SAFE_ALPHABET)}


# ── Encoding ──────────────────────────────────────────────────────────────────

def encode(number: int, min_length: int = 0) -> str:
    """
    Encode a non-negative integer to a Base-60 string using the HEXAGEN-60 alphabet.

    Args:
        number:     Non-negative integer to encode.
        min_length: Pad result with leading zeros to this length (optional).

    Returns:
        Base-60 encoded string.

    Raises:
        ValueError: If number is negative.

    Examples:
        >>> encode(0)
        '0'
        >>> encode(59)
        '★'
        >>> encode(60)
        '10'
        >>> encode(3600)
        '100'
    """
    if number < 0:
        raise ValueError(f"encode() requires a non-negative integer, got {number}")

    if number == 0:
        result = ALPHABET[0]
    else:
        digits: list[str] = []
        n = number
        while n:
            n, remainder = divmod(n, BASE)
            digits.append(ALPHABET[remainder])
        result = "".join(reversed(digits))

    return result.zfill(min_length) if min_length else result


def encode_url(number: int, min_length: int = 0) -> str:
    """
    Encode using the URL-safe variant (★→$ and ☆→_).
    Use this when embedding IDs in URLs without percent-encoding.

    Examples:
        >>> encode_url(58)
        '$'
        >>> encode_url(59)
        '_'
    """
    standard = encode(number, min_length)
    return standard.replace("\u2605", "$").replace("\u2606", "_")


# ── Decoding ──────────────────────────────────────────────────────────────────

def decode(encoded: str) -> int:
    """
    Decode a Base-60 HEXAGEN-60 string back to an integer.

    Args:
        encoded: Base-60 encoded string (standard or URL-safe).

    Returns:
        Decoded integer.

    Raises:
        ValueError: If string contains characters not in the alphabet.

    Examples:
        >>> decode('0')
        0
        >>> decode('10')
        60
        >>> decode('100')
        3600
    """
    if not encoded:
        raise ValueError("Cannot decode empty string")

    # Accept both standard and URL-safe variants
    normalised = encoded.replace("$", "\u2605").replace("_", "\u2606")

    result = 0
    for char in normalised:
        if char not in _CHAR_TO_VAL:
            raise ValueError(
                f"Invalid character '{char}' (U+{ord(char):04X}) "
                f"not in HEXAGEN-60 alphabet."
            )
        result = result * BASE + _CHAR_TO_VAL[char]

    return result


def decode_url(encoded: str) -> int:
    """Decode a URL-safe Base-60 string ($ and _ variants accepted)."""
    return decode(encoded)   # decode() already normalises URL-safe chars


# ── Utilities ─────────────────────────────────────────────────────────────────

def is_valid(encoded: str, *, allow_url_safe: bool = True) -> bool:
    """
    Return True if every character in `encoded` belongs to the HEXAGEN-60 alphabet.

    Args:
        encoded:        String to validate.
        allow_url_safe: Accept $ and _ as URL-safe equivalents of ★ and ☆.

    Examples:
        >>> is_valid("B4xq")
        True
        >>> is_valid("INVALID!")
        False
    """
    check_set = set(_CHAR_TO_VAL)
    if allow_url_safe:
        check_set |= {"$", "_"}
    return bool(encoded) and all(ch in check_set for ch in encoded)


def pad(encoded: str, length: int, char: str = "0") -> str:
    """
    Left-pad a Base-60 string to at least `length` characters.

    Examples:
        >>> pad("1", 4)
        '0001'
    """
    return encoded.rjust(length, char)
