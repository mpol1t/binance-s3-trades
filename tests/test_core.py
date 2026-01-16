from datetime import date

import pytest

from binance_s3_trades.core import (
    build_key_filter,
    filter_trade_keys,
    is_trade_zip_key,
    key_month,
    key_symbol,
    matches_filter,
    normalize_symbols,
    parse_month,
)
from binance_s3_trades.types import KeyFilter


def test_parse_month_valid_returns_first_day():
    assert parse_month("2024-02") == date(2024, 2, 1)


def test_parse_month_none_returns_none():
    assert parse_month(None) is None
    assert parse_month("") is None


@pytest.mark.xfail(
    reason="Docstring says invalid returns None, but current implementation raises ValueError.",
    strict=True,
)
def test_parse_month_invalid_returns_none_per_docstring():
    assert parse_month("2024-13") is None  # invalid month


def test_parse_month_invalid_current_behavior_raises_value_error():
    with pytest.raises(ValueError):
        parse_month("2024-13")


@pytest.mark.parametrize(
    "raw, expected",
    [
        (["btcusdt"], frozenset({"BTCUSDT"})),
        (["btcusdt", "BTCUSDT"], frozenset({"BTCUSDT"})),
        (["ethusdt", "btcusdt"], frozenset({"ETHUSDT", "BTCUSDT"})),
    ],
)
def test_normalize_symbols_uppercases_and_dedups(raw, expected):
    assert normalize_symbols(raw) == expected


@pytest.mark.parametrize("raw", [None, [], ()])
def test_normalize_symbols_none_or_empty_returns_none(raw):
    assert normalize_symbols(raw) is None


def test_build_key_filter_wires_parsing_and_normalization():
    flt = build_key_filter(symbols=["btcusdt"], start="2024-01", end="2024-03")
    assert flt.symbols == frozenset({"BTCUSDT"})
    assert flt.start_month == date(2024, 1, 1)
    assert flt.end_month == date(2024, 3, 1)


@pytest.mark.parametrize(
    "key, expected",
    [
        ("BTCUSDT-trades-2024-01.zip", True),
        ("BTCUSDT-trades-2024-01.CHECKSUM.zip", False),
        ("BTCUSDT-trades-2024-01.csv", False),
        ("notzip", False),
    ],
)
def test_is_trade_zip_key(key, expected):
    assert is_trade_zip_key(key) is expected


def test_key_symbol_requires_prefix_match(s3_prefix: str):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    assert key_symbol(s3_prefix, key) == "BTCUSDT"
    assert key_symbol("wrong/prefix/", key) is None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("data/spot/monthly/trades/BTCUSDT/BTCUSDT-trades-2024-01.zip", date(2024, 1, 1)),
        ("BTCUSDT-trades-2024-12.zip", date(2024, 12, 1)),
        ("BTCUSDT-trades-2024-00.zip", None),  # invalid month
        ("BTCUSDT-trades-2024.zip", None),  # not enough segments
        ("BTCUSDT-trades-2024-01.CHECKSUM.zip", None),  # not a trade zip key
        ("BTCUSDT-trades-2024-01.csv", None),
    ],
)
def test_key_month_parsing(key, expected):
    assert key_month(key) == expected


def test_matches_filter_rejects_non_trade_keys(s3_prefix: str):
    flt = KeyFilter(symbols=None, start_month=None, end_month=None)
    assert matches_filter("not-a-zip", prefix=s3_prefix, flt=flt) is False


def test_matches_filter_symbol_filtering(s3_prefix: str):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    flt = KeyFilter(symbols=frozenset({"BTCUSDT"}), start_month=None, end_month=None)
    assert matches_filter(key, prefix=s3_prefix, flt=flt) is True

    flt_other = KeyFilter(symbols=frozenset({"ETHUSDT"}), start_month=None, end_month=None)
    assert matches_filter(key, prefix=s3_prefix, flt=flt_other) is False

    # Prefix mismatch -> key_symbol None -> should fail when symbols filter is set
    assert matches_filter(key, prefix="wrong/prefix/", flt=flt) is False


@pytest.mark.parametrize(
    "start,end,month,expected",
    [
        ("2024-01", None, "2024-01", True),  # inclusive lower bound
        ("2024-02", None, "2024-01", False),  # below start
        (None, "2024-02", "2024-02", True),  # inclusive upper bound
        (None, "2024-02", "2024-03", False),  # above end
        ("2024-02", "2024-03", "2024-02", True),
        ("2024-02", "2024-03", "2024-03", True),
    ],
)
def test_matches_filter_date_bounds_inclusive(s3_prefix: str, start, end, month, expected):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-{month}.zip"
    flt = build_key_filter(symbols=None, start=start, end=end)
    assert matches_filter(key, prefix=s3_prefix, flt=flt) is expected


def test_filter_trade_keys_filters_and_sorts(sample_keys: list[str], s3_prefix: str):
    flt = build_key_filter(symbols=["BTCUSDT"], start="2024-02", end="2024-03")
    result = filter_trade_keys(sample_keys, prefix=s3_prefix, flt=flt)

    # Only BTCUSDT Feb is present in sample_keys; BTC Mar isn't in the list.
    assert result == [f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-02.zip"]
