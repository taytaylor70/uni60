"""
tests/test_uni60.py
─────────────────────────────────────────────────────────────────────────────
HEXAGEN-60 Protocol — Test Suite
Taylor Dynasty Systems | v1.0.0

Run with:
    pytest tests/ -v
    pytest tests/ -v --tb=short
    pytest tests/ -v --cov=uni60 --cov-report=term-missing
─────────────────────────────────────────────────────────────────────────────
"""

import time
import threading
import pytest

import uni60
from uni60 import (
    ALPHABET, BASE,
    encode, decode, encode_url, decode_url, is_valid, pad,
    checksum_compute, checksum_verify, checksum_append,
    TypePrefix, Generator, generate, inspect,
)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — ALPHABET INVARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAlphabet:
    def test_length_is_60(self):
        assert len(ALPHABET) == 60

    def test_base_is_60(self):
        assert BASE == 60

    def test_no_duplicate_characters(self):
        assert len(set(ALPHABET)) == 60

    def test_no_ambiguous_characters(self):
        """I, O, l, o must be absent to prevent visual ambiguity."""
        for ch in ("I", "O", "l", "o"):
            assert ch not in ALPHABET, f"Ambiguous character '{ch}' found in alphabet"

    def test_extended_symbols_present(self):
        assert "\u2605" in ALPHABET   # ★
        assert "\u2606" in ALPHABET   # ☆

    def test_alphabet_index_integrity(self):
        """Every character must round-trip through encode/decode."""
        for i, ch in enumerate(ALPHABET):
            encoded = encode(i)
            assert decode(encoded) == i


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — CORE ENCODING
# ─────────────────────────────────────────────────────────────────────────────

class TestEncode:
    def test_zero(self):
        assert encode(0) == "0"

    def test_single_digits(self):
        # Digits 0–9 → indices 0–9
        assert encode(9)  == "9"
        # Uppercase (no I, O) → indices 10–33
        assert encode(10) == "A"
        assert encode(33) == "Z"
        # Lowercase (no l, o) → indices 34–57
        assert encode(34) == "a"
        assert encode(57) == "z"   # last lowercase
        # Extended Unicode symbols → indices 58–59
        assert encode(58) == "\u2605"   # ★
        assert encode(59) == "\u2606"   # ☆

    def test_base_boundary(self):
        assert encode(60)   == "10"
        assert encode(3600) == "100"

    def test_large_number(self):
        """2^32 should encode to ~6 base-60 chars."""
        n = 2 ** 32
        encoded = encode(n)
        assert decode(encoded) == n
        assert len(encoded) <= 7

    def test_min_length_padding(self):
        assert encode(0, min_length=4)  == "0000"
        assert encode(1, min_length=4)  == "0001"
        assert encode(60, min_length=2) == "10"

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            encode(-1)


class TestDecode:
    def test_zero(self):
        assert decode("0") == 0

    def test_round_trips(self):
        for n in [0, 1, 59, 60, 3599, 3600, 12345678, 2**32, 2**48]:
            assert decode(encode(n)) == n

    def test_url_safe_chars(self):
        """$ and _ should decode as ★ and ☆ equivalents."""
        assert decode("$") == 58
        assert decode("_") == 59

    def test_invalid_character_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            decode("!")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            decode("")


class TestEncodeUrl:
    def test_replaces_star(self):
        assert "\u2605" not in encode_url(58)
        assert encode_url(58) == "$"

    def test_replaces_star_2(self):
        assert "\u2606" not in encode_url(59)
        assert encode_url(59) == "_"

    def test_round_trip(self):
        for n in range(200):
            assert decode_url(encode_url(n)) == n


class TestIsValid:
    def test_valid_strings(self):
        assert is_valid("0") is True
        assert is_valid("ABC123") is True
        assert is_valid("\u2605\u2606") is True

    def test_url_safe_variants(self):
        assert is_valid("$_") is True   # URL-safe mode

    def test_invalid_strings(self):
        assert is_valid("!") is False
        assert is_valid("I") is False   # ambiguous, excluded
        assert is_valid("") is False

    def test_mixed_valid_invalid(self):
        assert is_valid("B4x!") is False


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — CHECKSUM
# ─────────────────────────────────────────────────────────────────────────────

class TestChecksum:
    def test_compute_returns_single_char(self):
        ch = checksum_compute("B4xq")
        assert len(ch) == 1
        assert ch in ALPHABET

    def test_append_adds_one_char(self):
        result = checksum_append("B4xq")
        assert len(result) == 5
        assert result.startswith("B4xq")

    def test_verify_valid(self):
        with_check = checksum_append("B4xq")
        assert checksum_verify(with_check) is True

    def test_verify_detects_corruption(self):
        with_check = checksum_append("B4xq")
        # Corrupt the checksum digit
        corrupted = with_check[:-1] + ("A" if with_check[-1] != "A" else "B")
        assert checksum_verify(corrupted) is False

    def test_verify_detects_transposition(self):
        """Luhn should catch adjacent swaps."""
        payload = "B4xq"
        with_check = checksum_append(payload)
        # Swap first two payload chars
        swapped = with_check[1] + with_check[0] + with_check[2:]
        assert checksum_verify(swapped) is False

    def test_verify_short_string_false(self):
        assert checksum_verify("A") is False

    def test_deterministic(self):
        """Same payload always yields same check char."""
        assert checksum_compute("B4xq") == checksum_compute("B4xq")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — ID GENERATION
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerator:
    EPOCH = 1_704_067_200   # 2024-01-01

    def test_generates_11_chars(self):
        gen = Generator(epoch=self.EPOCH)
        id_ = gen.generate(TypePrefix.USER)
        assert len(id_) == 11, f"Expected 11 chars, got {len(id_)}: {id_!r}"

    def test_type_prefix_embedded(self):
        gen = Generator(epoch=self.EPOCH)
        id_ = gen.generate(TypePrefix.USER)
        assert id_[0] == TypePrefix.USER

    def test_unique_ids(self):
        gen = Generator(epoch=self.EPOCH)
        ids = {gen.generate(TypePrefix.EVENT) for _ in range(1000)}
        assert len(ids) == 1000, "Duplicate IDs generated"

    def test_checksum_valid(self):
        gen = Generator(epoch=self.EPOCH)
        for _ in range(50):
            id_ = gen.generate(TypePrefix.ASSET)
            info = gen.inspect(id_)
            assert info.checksum_valid, f"Bad checksum in {id_!r}"

    def test_thread_safety(self):
        gen = Generator(epoch=self.EPOCH)
        results: list[str] = []
        lock = threading.Lock()

        def worker():
            for _ in range(200):
                id_ = gen.generate(TypePrefix.SYSTEM)
                with lock:
                    results.append(id_)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 2000
        assert len(set(results)) == 2000, "Thread safety violation: duplicate IDs"

    def test_inspect_round_trip(self):
        gen = Generator(epoch=self.EPOCH)
        ts  = int(time.time())
        id_ = gen.generate(TypePrefix.DOC, timestamp=ts)
        info = gen.inspect(id_)

        assert info.type_name == "DOC"
        assert info.type_prefix == TypePrefix.DOC
        assert info.checksum_valid is True
        assert info.epoch == self.EPOCH

    def test_different_types_same_timestamp(self):
        gen = Generator(epoch=self.EPOCH)
        ts  = int(time.time())
        ids = [gen.generate(tp, timestamp=ts) for tp in (
            TypePrefix.USER, TypePrefix.EVENT, TypePrefix.ASSET
        )]
        # Different type prefix → different first char
        first_chars = [id_[0] for id_ in ids]
        assert len(set(first_chars)) == 3


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — MODULE-LEVEL CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestModuleLevelAPI:
    def test_generate_returns_11_chars(self):
        id_ = generate(TypePrefix.ORG)
        assert len(id_) == 11

    def test_inspect_valid_id(self):
        id_  = generate(TypePrefix.USER)
        info = inspect(id_)
        assert info.type_name == "USER"
        assert info.checksum_valid is True

    def test_inspect_wrong_length_raises(self):
        with pytest.raises(ValueError, match="11-character"):
            inspect("short")

    def test_generate_inspect_round_trip(self):
        for tp_name in ("ORG", "EVENT", "ASSET", "USER", "DOC"):
            tp   = TypePrefix.from_name(tp_name)
            id_  = generate(tp)
            info = inspect(id_)
            assert info.type_name == tp_name
            assert info.checksum_valid is True


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — TYPE PREFIX REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

class TestTypePrefix:
    def test_known_names(self):
        for name in ("ORG", "EVENT", "ASSET", "USER", "DOC", "LOC", "METRIC", "SYSTEM", "CUSTOM"):
            prefix = TypePrefix.from_name(name)
            assert TypePrefix.name(prefix) == name

    def test_case_insensitive(self):
        assert TypePrefix.from_name("user") == TypePrefix.from_name("USER")

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown type name"):
            TypePrefix.from_name("BOGUS")

    def test_unknown_prefix_returns_unknown(self):
        result = TypePrefix.name("\uF000")
        assert "UNKNOWN" in result


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — INTEGRATION / END-TO-END
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    def test_multi_type_batch(self):
        """Generate 100 IDs of each type; all unique; all valid checksums."""
        gen   = Generator()
        all_ids: list[str] = []

        for tp_name in ("ORG", "EVENT", "ASSET", "USER", "DOC"):
            tp = TypePrefix.from_name(tp_name)
            batch = [gen.generate(tp) for _ in range(100)]
            all_ids.extend(batch)
            for id_ in batch:
                info = gen.inspect(id_)
                assert info.checksum_valid
                assert info.type_name == tp_name

        # Global uniqueness across all types in same batch
        assert len(set(all_ids)) == len(all_ids)

    def test_version_exported(self):
        assert uni60.__version__ == "1.0.0"

    def test_full_api_surface(self):
        """Smoke test every exported name in __all__."""
        for name in uni60.__all__:
            assert hasattr(uni60, name), f"Missing export: {name}"
