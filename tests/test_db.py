"""Tests for velodex.db helpers."""
import pytest

from velodex.db import normalize_birth_date


@pytest.mark.parametrize(
    "raw,expected",
    [
        # UCI native format: DD.MM.YYYY
        ("03.09.2001", "2001-09-03"),
        ("21.09.1998", "1998-09-21"),
        ("25.05.1986", "1986-05-25"),  # day > 12, previously misparsed
        ("13.01.2002", "2002-01-13"),
        # Already ISO -> passthrough
        ("2001-09-03", "2001-09-03"),
        # Slash-separated DD/MM/YYYY (admin override convenience)
        ("03/09/2001", "2001-09-03"),
    ],
)
def test_normalizes_known_formats(raw, expected):
    assert normalize_birth_date(raw) == expected


@pytest.mark.parametrize("value", [None, ""])
def test_passes_through_empty(value):
    assert normalize_birth_date(value) == value


@pytest.mark.parametrize("value", ["garbage", "not-a-date", "99.99.9999"])
def test_unparseable_returned_unchanged(value):
    # Malformed values are preserved rather than silently dropped.
    assert normalize_birth_date(value) == value
