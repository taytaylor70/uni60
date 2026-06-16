# uni60

**HEXAGEN-60 Protocol** — Hierarchical Unicode Base-60 Encoding for Distributed Systems

[![CI](https://github.com/taylordynasty/uni60/actions/workflows/ci.yml/badge.svg)](https://github.com/taylordynasty/uni60/actions)
[![PyPI version](https://badge.fury.io/py/uni60.svg)](https://badge.fury.io/py/uni60)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

> *The encoding system ancient Babylon used to measure time — rebuilt for modern distributed architecture.*

---

## The Problem With UUID

Every distributed system needs unique identifiers. The default answer is UUID v4:

```
550e8400-e29b-41d4-a716-446655440000
```

UUID v4 guarantees uniqueness. But it encodes **nothing else**:

| Property | UUID v4 | HEXAGEN-60 |
|---|:---:|:---:|
| Globally unique | ✅ | ✅ |
| Hierarchical structure | ❌ | ✅ |
| Time-ordered | ❌ | ✅ |
| Semantic type encoding | ❌ | ✅ |
| Checksum / error detection | ❌ | ✅ |
| Compact (shorter) | ❌ | ✅ 11 vs 36 chars |
| Human-inspectable | ❌ | ✅ |

---

## What Is HEXAGEN-60?

**HEXAGEN-60** (Hierarchical Encoding & eXpressive Address GENeration — Base-60) is an identifier protocol built on two ancient, proven systems:

**1. Base-60 (Sexagesimal arithmetic)** — the Babylonian numeral system, still used today for time (60 seconds, 60 minutes) and angles (360° = 6×60). Base-60 has 12 factors, making it the most evenly divisible base below 120 — ideal for hierarchical partitioning.

**2. Unicode's hierarchical plane structure** — Unicode organizes 1,114,112 code points across 17 planes and 308 named blocks. Its Private Use Areas (U+E000–U+F8FF) provide 6,400 code points specifically for custom applications.

The result: IDs that are **shorter**, **hierarchical**, **time-aware**, **semantically typed**, and **self-validating**.

---

## Quick Start

```bash
pip install uni60
```

```python
import uni60
from uni60 import generate, inspect, TypePrefix

# Generate typed IDs
user_id  = generate(TypePrefix.USER)    # '\ue003B4xq7m09C'
event_id = generate(TypePrefix.EVENT)   # '\ue001B4xq7m0AC'
asset_id = generate(TypePrefix.ASSET)   # '\ue002B4xq7m0BC'

# Inspect any ID
info = inspect(user_id)
print(info.type_name)       # 'USER'
print(info.era)             # 730  (days since epoch)
print(info.period)          # 43200  (seconds into today)
print(info.sequence)        # 0
print(info.checksum_valid)  # True

# Raw Base-60 encoding
uni60.encode(3600)   # '100'
uni60.decode('100')  # 3600
```

---

## ID Structure

```
[ TYPE:1 ][ ERA:2 ][ PERIOD:3 ][ SEQUENCE:4 ][ CHECK:1 ]
  ──────── ──────── ──────────  ─────────────  ─────────
  Unicode   Days     Seconds     12.96M unique  Luhn-60
  PUA char  since    within      IDs per        checksum
            epoch    day         period
```

**Example:**
```
\uE003 B4 xq7 m09C
  │    │   │   │  └─ Luhn-60 checksum
  │    │   │   └──── Sequence (base-60, up to 12,960,000/second)
  │    │   └──────── Period (base-60, seconds within day)
  │    └──────────── Era (base-60, days since epoch)
  └───────────────── Type = USER (U+E003)
```

Total length: **11 characters** vs UUID's **36 characters**.

---

## The Base-60 Alphabet

60 unambiguous, carefully chosen characters:

```python
ALPHABET = (
    "0123456789"          # digits      (0–9)
    "ABCDEFGHJKLMNPQRSTUVWXYZ"  # uppercase  (10–33) — no I, O
    "abcdefghjkmnpqrstuvwxyz"   # lowercase  (34–57) — no l, o
    "★☆"                  # extended   (58–59) — U+2605, U+2606
)
```

Visual ambiguity eliminated: **I** and **l** (look like `1`), **O** and **o** (look like `0`) are excluded.

---

## Type Prefixes

HEXAGEN-60 uses Unicode Private Use Area characters as semantic type markers:

| Name | Char | Code Point | Use Case |
|---|---|---|---|
| `ORG` | (private) | U+E000 | Organisations, companies, teams |
| `EVENT` | (private) | U+E001 | Events, transactions, logs |
| `ASSET` | (private) | U+E002 | Assets, resources, files |
| `USER` | (private) | U+E003 | Users, identities, accounts |
| `DOC` | (private) | U+E004 | Documents, records, contracts |
| `LOC` | (private) | U+E005 | Locations, coordinates |
| `METRIC` | (private) | U+E006 | Measurements, metrics |
| `SYSTEM` | (private) | U+E007 | System/infrastructure nodes |
| `CUSTOM` | (private) | U+E008 | User-defined |

```python
from uni60 import TypePrefix

TypePrefix.from_name("USER")   # Returns the U+E003 character
TypePrefix.name("\uE003")      # Returns "USER"
```

---

## Capacity

| Component | Encoding | Capacity |
|---|---|---|
| ERA (2 chars) | Base-60² = 3,600 values | ~9.8 years of daily resolution |
| PERIOD (3 chars) | Base-60³ = 216,000 values | 2.5 days of second resolution |
| SEQUENCE (4 chars) | Base-60⁴ = 12,960,000 values | 12.96M unique IDs per second |
| **Total per type** | | **~4.6 × 10¹⁶ unique IDs** |

---

## Compactness Comparison

For a 64-bit (2⁶⁴) address space:

| System | Characters | Base | Hierarchical | Typed |
|---|---|---|---|---|
| UUID v4 | 36 | 16 | ❌ | ❌ |
| ULID | 26 | 32 | ❌ | ❌ |
| KSUID | 27 | 62 | ❌ | ❌ |
| Base64 | 11 | 64 | ❌ | ❌ |
| **HEXAGEN-60** | **11** | **60** | ✅ | ✅ |

HEXAGEN-60 matches Base-64's compactness while adding hierarchy, typing, and twelve-way divisibility.

---

## Thread Safety

The `Generator` class is thread-safe. Sequence numbers are guaranteed unique within each second, even under concurrent load:

```python
from uni60 import Generator, TypePrefix
import threading

gen = Generator()
results = []
lock = threading.Lock()

def worker():
    for _ in range(1000):
        id_ = gen.generate(TypePrefix.EVENT)
        with lock:
            results.append(id_)

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()

assert len(set(results)) == 10_000  # All unique
```

---

## URL-Safe Mode

The extended symbols `★` and `☆` require percent-encoding in URLs. Use `encode_url()` for URL-safe output:

```python
from uni60 import encode_url, decode_url

encode_url(58)   # '$'  (instead of '★')
encode_url(59)   # '_'  (instead of '☆')
decode_url("$")  # 58
decode_url("_")  # 59
```

---

## Running the Examples

```bash
git clone https://github.com/taylordynasty/uni60
cd uni60
pip install -e ".[dev]"
python examples/quickstart.py
```

---

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=uni60 --cov-report=term-missing
```

---

## API Reference

### Core Encoding

| Function | Description |
|---|---|
| `encode(n, min_length=0)` | Encode integer to Base-60 string |
| `decode(s)` | Decode Base-60 string to integer |
| `encode_url(n)` | URL-safe variant (★→$ ☆→_) |
| `decode_url(s)` | Decode URL-safe Base-60 string |
| `is_valid(s)` | Validate alphabet membership |
| `pad(s, length)` | Left-pad with leading zeros |

### Checksum

| Function | Description |
|---|---|
| `checksum_compute(payload)` | Compute Luhn-60 check character |
| `checksum_verify(encoded)` | Verify last char is valid checksum |
| `checksum_append(payload)` | Append checksum to payload |

### ID Generation

| Class/Function | Description |
|---|---|
| `generate(type_prefix, timestamp)` | Generate a HEXAGEN-60 ID |
| `inspect(id)` | Decode and inspect an ID |
| `Generator(epoch, type_prefix)` | Thread-safe generator instance |
| `TypePrefix` | Type prefix constants and registry |
| `Hex60ID` | Decoded ID dataclass |

---

## Roadmap

- [ ] JavaScript/TypeScript port (`@taylordynasty/uni60`)
- [ ] Go port (`github.com/taylordynasty/uni60-go`)
- [ ] Rust crate (`uni60`)
- [ ] REST API service (HEXAGEN-60-as-a-Service)
- [ ] HEXAGEN-60 RFC draft
- [ ] PostgreSQL extension for native ID support
- [ ] Database-specific integration guides (PostgreSQL, MySQL, MongoDB, Redis)

---

## Contributing

Contributions welcome. Please open an issue first for significant changes.

```bash
git clone https://github.com/taylordynasty/uni60
cd uni60
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Why "uni60"?

**uni** — Universal (Unicode + unified) | **60** — Base-60 (sexagesimal)

---

## License

MIT © 2026 Taylor Dynasty Systems

---

## Citation

If you use HEXAGEN-60 in research or published work:

```bibtex
@software{hexagen60_2026,
  title   = {uni60: HEXAGEN-60 Hierarchical Unicode Base-60 Encoding Protocol},
  author  = {Taylor Dynasty Systems},
  year    = {2026},
  url     = {https://github.com/taylordynasty/uni60},
  version = {1.0.0}
}
```

---

*Built by [Taylor Dynasty Systems](https://taylordynasty.com) — creating the primitives that systems run on.*
