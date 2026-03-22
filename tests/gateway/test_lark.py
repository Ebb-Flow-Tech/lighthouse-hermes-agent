# tests/gateway/test_lark.py
import json
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gateway.config import Platform, PlatformConfig
from gateway.platforms.lark import LarkAdapter, check_lark_requirements


def _make_config(**extra_overrides):
    """Create a minimal PlatformConfig for Lark tests."""
    config = PlatformConfig(enabled=True)
    config.extra = {
        "app_id": "test_app_id",
        "app_secret": "test_secret",
        "verification_token": "test_token",
        "encrypt_key": "",
        **extra_overrides,
    }
    return config


class TestCheckRequirements:
    def test_returns_true_when_deps_available(self):
        assert check_lark_requirements() is True


class TestLarkAdapterInit:
    def test_initializes_with_config(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        assert adapter.name == "Lark"
        assert adapter.is_connected is False


class TestSignatureVerification:
    def test_valid_signature_passes(self):
        config = _make_config(encrypt_key="test_encrypt_key")
        adapter = LarkAdapter(config)

        timestamp = "1234567890"
        nonce = "test_nonce"
        body = '{"test": "data"}'
        content = timestamp + nonce + "test_encrypt_key" + body
        expected_sig = hashlib.sha256(content.encode()).hexdigest()

        assert adapter._verify_signature(expected_sig, timestamp, nonce, body) is True

    def test_invalid_signature_fails(self):
        config = _make_config(encrypt_key="test_encrypt_key")
        adapter = LarkAdapter(config)
        assert adapter._verify_signature("bad_sig", "ts", "nonce", "body") is False

    def test_no_encrypt_key_skips_verification(self):
        config = _make_config(encrypt_key="")
        adapter = LarkAdapter(config)
        assert adapter._verify_signature("anything", "ts", "nonce", "body") is True


class TestEventDeduplication:
    def test_first_event_is_not_duplicate(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        assert adapter._is_duplicate("evt_1") is False

    def test_second_same_event_is_duplicate(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        adapter._is_duplicate("evt_1")
        assert adapter._is_duplicate("evt_1") is True


class TestContentDetection:
    def test_detects_markdown_table(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        text = "| col1 | col2 |\n|------|------|\n| a | b |"
        assert adapter._has_markdown_table(text) is True

    def test_rejects_non_table_text(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        assert adapter._has_markdown_table("Just some text") is False


class TestParseMarkdownTable:
    def _make_adapter(self):
        return LarkAdapter(_make_config())

    def test_parses_simple_table(self):
        adapter = self._make_adapter()
        text = "| name | age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
        result = adapter._parse_markdown_table(text)
        assert result is not None
        assert result["columns"] == ["name", "age"]
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "Alice"

    def test_extracts_title_from_text_before_table(self):
        adapter = self._make_adapter()
        text = "**Top Users**\n| name | score |\n|------|-------|\n| Alice | 100 |"
        result = adapter._parse_markdown_table(text)
        assert result is not None
        assert result["title"] == "Top Users"

    def test_defaults_title_when_no_prefix(self):
        adapter = self._make_adapter()
        text = "| col |\n|-----|\n| val |"
        result = adapter._parse_markdown_table(text)
        assert result is not None
        assert result["title"] == "Query Results"

    def test_returns_none_for_non_table(self):
        adapter = self._make_adapter()
        assert adapter._parse_markdown_table("Just text") is None


class TestConcurrency:
    def test_active_calls_starts_at_zero(self):
        config = _make_config()
        adapter = LarkAdapter(config)
        assert adapter._active_calls == 0
