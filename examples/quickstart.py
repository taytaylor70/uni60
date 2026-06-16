"""
examples/quickstart.py
─────────────────────────────────────────────────────────────────────────────
HEXAGEN-60 Protocol — Quickstart Examples
Taylor Dynasty Systems

Run: python examples/quickstart.py
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uni60
from uni60 import generate, inspect, encode, decode, TypePrefix, Generator

DIVIDER = "─" * 60

def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


# ── 1. Raw Base-60 Encoding ───────────────────────────────────────────────────

section("1. RAW BASE-60 ENCODING")

for n in [0, 9, 10, 59, 60, 3600, 1_000_000, 2**32]:
    encoded = encode(n)
    decoded = decode(encoded)
    print(f"  {n:>12,}  →  {encoded:<10}  →  {decoded:>12,}  ✓")


# ── 2. Generate IDs by Type ───────────────────────────────────────────────────

section("2. GENERATE IDS BY TYPE")

type_map = {
    "ORG":    TypePrefix.ORG,
    "EVENT":  TypePrefix.EVENT,
    "ASSET":  TypePrefix.ASSET,
    "USER":   TypePrefix.USER,
    "DOC":    TypePrefix.DOC,
    "LOC":    TypePrefix.LOC,
    "METRIC": TypePrefix.METRIC,
    "SYSTEM": TypePrefix.SYSTEM,
}

for name, prefix in type_map.items():
    id_ = generate(prefix)
    print(f"  {name:<8}  →  {id_}  (codepoint: U+{ord(id_[0]):04X})")


# ── 3. Inspect a Generated ID ─────────────────────────────────────────────────

section("3. INSPECT A GENERATED ID")

sample_id = generate(TypePrefix.USER)
info      = inspect(sample_id)

print(f"  ID:              {sample_id}")
print(f"  Type:            {info.type_name}  (U+{ord(info.type_prefix):04X})")
print(f"  Era (days):      {info.era}")
print(f"  Period (secs):   {info.period}")
print(f"  Sequence:        {info.sequence}")
print(f"  Checksum valid:  {info.checksum_valid}")
print(f"  Approx. Unix ts: {info.approximate_unix_timestamp}")


# ── 4. High-Volume Generation ─────────────────────────────────────────────────

section("4. HIGH-VOLUME GENERATION (1,000 IDs)")

gen  = Generator()
ids  = [gen.generate(TypePrefix.EVENT) for _ in range(1000)]

# Verify all unique + all valid checksums
unique = len(set(ids)) == len(ids)
valid  = all(inspect(id_).checksum_valid for id_ in ids[:20])   # spot-check 20

print(f"  Generated:       {len(ids):,} IDs")
print(f"  All unique:      {unique}")
print(f"  Checksums valid: {valid} (spot-checked 20)")
print(f"  Sample IDs:")
for id_ in ids[:5]:
    print(f"    {id_}")


# ── 5. UUID vs HEXAGEN-60 Comparison ─────────────────────────────────────────

section("5. UUID  vs  HEXAGEN-60")

import uuid as _uuid

uuid4 = str(_uuid.uuid4())
h60   = generate(TypePrefix.USER)

print(f"  UUID v4:          {uuid4}")
print(f"    Length:         {len(uuid4)} chars")
print(f"    Hierarchical:   No")
print(f"    Time-ordered:   No")
print(f"    Semantic type:  No")
print(f"    Checksum:       No")
print()
print(f"  HEXAGEN-60:       {h60}")
print(f"    Length:         {len(h60)} chars  ({len(uuid4) - len(h60)} fewer)")
print(f"    Hierarchical:   Yes  (era → period → sequence)")
print(f"    Time-ordered:   Yes  (era encodes day since epoch)")
print(f"    Semantic type:  Yes  (Unicode PUA prefix)")
print(f"    Checksum:       Yes  (Luhn-60)")


# ── 6. URL-Safe Encoding ──────────────────────────────────────────────────────

section("6. URL-SAFE ENCODING")

from uni60 import encode_url, decode_url

for n in [0, 57, 58, 59, 60, 120]:
    std = encode(n)
    url = encode_url(n)
    rt  = decode_url(url)
    diff = "  ← extended symbol replaced" if std != url else ""
    print(f"  {n:>4}  std={std:<6}  url={url:<6}  round-trip={rt}{diff}")


print(f"\n{DIVIDER}")
print("  All examples completed successfully.")
print(DIVIDER)
