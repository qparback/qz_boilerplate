"""Tests for the API-key hashing helper. No DB, no app."""

from api.security import hash_key


def test_hash_is_deterministic():
    assert hash_key("hello") == hash_key("hello")


def test_hash_differs_for_different_keys():
    assert hash_key("aaa") != hash_key("bbb")


def test_hash_length():
    # Truncated to 16 hex chars
    assert len(hash_key("anything")) == 16
