"""
uni60 — Universal Hierarchical Base-60 Encoding Library
════════════════════════════════════════════════════════
HEXAGEN-60 Protocol | Taylor Dynasty Systems | v1.0.0

A compact, hierarchical, time-aware, semantically meaningful identifier
system built on Base-60 arithmetic and Unicode's hierarchical plane
structure.

Quick Start
───────────
    >>> import uni60
    >>> from uni60 import generate, inspect, TypePrefix

    # Generate IDs
    >>> user_id  = generate(TypePrefix.USER)
    >>> event_id = generate(TypePrefix.EVENT)
    >>> asset_id = generate(TypePrefix.ASSET)

    # Inspect any ID
    >>> info = inspect(user_id)
    >>> info.type_name
    'USER'
    >>> info.checksum_valid
    True
    >>> info.sequence
    0

    # Raw Base-60 encoding
    >>> uni60.encode(3600)
    '100'
    >>> uni60.decode('100')
    3600

    # Thread-safe generator instance
    >>> gen = uni60.Generator(epoch=1_704_067_200)
    >>> gen.generate(TypePrefix.DOC)

Links
─────
    GitHub   : https://github.com/taylordynasty/uni60
    PyPI     : https://pypi.org/project/uni60
    Protocol : https://taylordynasty.com/hexagen60
    License  : MIT
"""

from .core      import ALPHABET, BASE, encode, decode, encode_url, decode_url, is_valid, pad
from .checksum  import compute as checksum_compute, verify as checksum_verify, append as checksum_append
from .generator import TypePrefix, Hex60ID, Generator, generate, inspect

__version__  = "1.0.0"
__author__   = "Taylor Dynasty Systems"
__license__  = "MIT"
__all__ = [
    # Core encoding
    "ALPHABET",
    "BASE",
    "encode",
    "decode",
    "encode_url",
    "decode_url",
    "is_valid",
    "pad",
    # Checksum
    "checksum_compute",
    "checksum_verify",
    "checksum_append",
    # Generator
    "TypePrefix",
    "Hex60ID",
    "Generator",
    "generate",
    "inspect",
    # Meta
    "__version__",
]
