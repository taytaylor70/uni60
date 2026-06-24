"""
uni60/generator.py
─────────────────────────────────────────────────────────────────────────────
HEXAGEN-60 Protocol — Hierarchical ID Generator
Taylor Dynasty Systems | v1.0.0

ID Structure (10 characters + 1 Unicode type prefix = 11 chars total):

  [TYPE:1][ERA:2][PERIOD:3][SEQUENCE:4][CHECK:1]
   ─────── ────── ──────── ─────────── ────────
   Unicode  Days   Seconds  12.96M IDs  Luhn-60
   PUA char since  within   per period  check
           epoch   day

Type Prefixes (Unicode Private Use Area — Plane 0, U+E000–U+F8FF):
  \uE000  ORG     — Organisational entities
  \uE001  EVENT   — Events and transactions
  \uE002  ASSET   — Assets and resources
  \uE003  USER    — Users and identities
  \uE004  DOC     — Documents and records
  \uE005  LOC     — Locations and coordinates
  \uE006  METRIC  — Measurements and metrics
  \uE007  SYSTEM  — System and infrastructure
  \uE008  CUSTOM  — User-defined (extend freely)

Capacity:
  ERA (2 chars, Base-60²)    : 3,600 days  ≈  9.8 years per era
  PERIOD (3 chars, Base-60³) : 216,000 seconds ≈ 2.5 days of second-resolution
  SEQUENCE (4 chars, Base-60⁴): 12,960,000 unique IDs per period
  Total address space per type: ~4.6 × 10¹⁶ unique IDs over 10 years
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Optional

from .core    import encode, decode, BASE
from .checksum import append, verify

__all__ = [
    "TypePrefix",
    "Hex60ID",
    "Generator",
    "generate",
    "inspect",
]

# ── Type Prefix Registry ──────────────────────────────────────────────────────

class TypePrefix:
    """Unicode Private Use Area characters for semantic type encoding."""
    ORG     = "\uE000"   # Organisational entities
    EVENT   = "\uE001"   # Events and transactions
    ASSET   = "\uE002"   # Assets and resources
    USER    = "\uE003"   # Users and identities
    DOC     = "\uE004"   # Documents and records
    LOC     = "\uE005"   # Locations and coordinates
    METRIC  = "\uE006"   # Measurements and metrics
    SYSTEM  = "\uE007"   # System and infrastructure
    CUSTOM  = "\uE008"   # User-defined

    _NAMES: dict[str, str] = {
        "\uE000": "ORG",
        "\uE001": "EVENT",
        "\uE002": "ASSET",
        "\uE003": "USER",
        "\uE004": "DOC",
        "\uE005": "LOC",
        "\uE006": "METRIC",
        "\uE007": "SYSTEM",
        "\uE008": "CUSTOM",
    }

    @classmethod
    def name(cls, prefix: str) -> str:
        """Return the human-readable name for a type prefix character."""
        codepoint = f"U+{ord(prefix):04X}"
        return cls._NAMES.get(prefix, f"UNKNOWN({codepoint})")

    @classmethod
    def from_name(cls, name: str) -> str:
        """Return the prefix character for a given type name (case-insensitive)."""
        reverse = {v: k for k, v in cls._NAMES.items()}
        key = name.upper()
        if key not in reverse:
            raise ValueError(
                f"Unknown type name '{name}'. "
                f"Valid names: {', '.join(reverse.keys())}"
            )
        return reverse[key]


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Hex60ID:
    """
    A fully decoded HEXAGEN-60 identifier.

    Attributes:
        raw:            The original ID string (with type prefix).
        type_prefix:    Unicode PUA character indicating entity type.
        type_name:      Human-readable type name (e.g., "USER").
        era:            Days since epoch (Base-60 encoded in 2 chars).
        period:         Seconds within the era day (Base-60 encoded in 3 chars).
        sequence:       Unique sequence number within this period.
        checksum_valid: Whether the Luhn-60 checksum is valid.
        epoch:          Unix timestamp used as the reference epoch.
    """
    raw:            str
    type_prefix:    str
    type_name:      str
    era:            int
    period:         int
    sequence:       int
    checksum_valid: bool
    epoch:          int

    @property
    def approximate_unix_timestamp(self) -> int:
        """Reconstruct an approximate Unix timestamp from era + period."""
        return self.epoch + (self.era * 86400) + self.period

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return (
            f"Hex60ID(raw={self.raw!r}, type={self.type_name}, "
            f"era={self.era}, period={self.period}, sequence={self.sequence}, "
            f"valid={self.checksum_valid})"
        )


# ── Generator ─────────────────────────────────────────────────────────────────

class Generator:
    """
    Thread-safe HEXAGEN-60 ID generator.

    Args:
        epoch:      Unix timestamp used as the reference point (default: 2024-01-01 UTC).
        type_prefix: Default type prefix character.

    Examples:
        >>> gen = Generator()
        >>> id1 = gen.generate(TypePrefix.USER)
        >>> id2 = gen.generate(TypePrefix.EVENT)
        >>> gen.inspect(id1)
        Hex60ID(raw='...', type='USER', ...)
    """

    DEFAULT_EPOCH: int = 1_704_067_200   # 2024-01-01 00:00:00 UTC

    def __init__(
        self,
        epoch: int = DEFAULT_EPOCH,
        type_prefix: str = TypePrefix.CUSTOM,
    ) -> None:
        self.epoch        = epoch
        self.type_prefix  = type_prefix
        self._lock        = threading.Lock()
        self._last_period = -1
        self._sequence    = 0

    def generate(
        self,
        type_prefix: Optional[str] = None,
        timestamp: Optional[int]   = None,
    ) -> str:
        """
        Generate a new HEXAGEN-60 identifier.

        Args:
            type_prefix: Override the generator's default type prefix.
            timestamp:   Unix timestamp (uses current time if None).

        Returns:
            11-character HEXAGEN-60 string.

        Thread safety:
            Safe to call from multiple threads; sequence numbers are
            guaranteed unique within the same second.
        """
        ts      = timestamp if timestamp is not None else int(time.time())
        prefix  = type_prefix or self.type_prefix
        elapsed = ts - self.epoch

        # Hierarchical time decomposition
        era    = elapsed // 86_400        # Day index since epoch
        period = elapsed %  86_400        # Second-of-day

        with self._lock:
            if period != self._last_period:
                self._last_period = period
                self._sequence    = 0
            else:
                self._sequence += 1
                if self._sequence >= BASE ** 4:    # 12,960,000 max per second
                    raise OverflowError(
                        f"Sequence exhausted for period {period}. "
                        "Maximum 12,960,000 IDs per second."
                    )
            seq = self._sequence

        era_part    = encode(era,    min_length=2)
        period_part = encode(period, min_length=3)
        seq_part    = encode(seq,    min_length=4)

        payload = f"{era_part}{period_part}{seq_part}"
        return f"{prefix}{append(payload)}"

    def inspect(self, hex60_id: str) -> Hex60ID:
        """
        Decode and inspect a HEXAGEN-60 identifier.

        Args:
            hex60_id: A HEXAGEN-60 string (11 characters with type prefix).

        Returns:
            Hex60ID dataclass with all decoded fields.

        Raises:
            ValueError: If the string length or format is invalid.
        """
        return inspect(hex60_id, epoch=self.epoch)


# ── Module-Level Convenience Functions ───────────────────────────────────────

_default_generator = Generator()


def generate(
    type_prefix: str = TypePrefix.CUSTOM,
    timestamp:   Optional[int] = None,
    epoch:       int = Generator.DEFAULT_EPOCH,
) -> str:
    """
    Generate a HEXAGEN-60 ID using the module-level default generator.

    Args:
        type_prefix: Unicode PUA character for entity type.
        timestamp:   Unix timestamp (uses time.time() if None).
        epoch:       Reference epoch (default: 2024-01-01 UTC).

    Returns:
        11-character HEXAGEN-60 string.

    Examples:
        >>> from uni60 import generate, TypePrefix
        >>> generate(TypePrefix.USER)
        '\ue003B4xq7mC3'
    """
    if epoch != Generator.DEFAULT_EPOCH:
        return Generator(epoch=epoch).generate(type_prefix, timestamp)
    return _default_generator.generate(type_prefix, timestamp)


def inspect(hex60_id: str, epoch: int = Generator.DEFAULT_EPOCH) -> Hex60ID:
    """
    Decode a HEXAGEN-60 identifier into its constituent parts.

    Args:
        hex60_id: Full HEXAGEN-60 string (11 chars).
        epoch:    Reference epoch used during generation.

    Returns:
        Hex60ID dataclass.

    Raises:
        ValueError: If the ID is malformed or the wrong length.

    Examples:
        >>> from uni60 import inspect
        >>> info = inspect('\ue003B4xq7mC3')
        >>> info.type_name
        'USER'
        >>> info.checksum_valid
        True
    """
    # Minimum: 1 prefix + 2 era + 3 period + 4 seq + 1 check = 11 chars
    if len(hex60_id) != 11:
        raise ValueError(
            f"Expected 11-character HEXAGEN-60 ID, got {len(hex60_id)} chars: {hex60_id!r}"
        )

    prefix     = hex60_id[0]
    era_enc    = hex60_id[1:3]
    period_enc = hex60_id[3:6]
    seq_enc    = hex60_id[6:10]
    # checksum is hex60_id[10]

    body = hex60_id[1:]   # Everything after the type prefix

    return Hex60ID(
        raw            = hex60_id,
        type_prefix    = prefix,
        type_name      = TypePrefix.name(prefix),
        era            = decode(era_enc),
        period         = decode(period_enc),
        sequence       = decode(seq_enc),
        checksum_valid = verify(body),
        epoch          = epoch,
    )
