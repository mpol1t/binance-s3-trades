import os
from datetime import date, datetime
from typing import FrozenSet, Iterable, Sequence

from binance_s3_trades.types import KeyFilter, Symbol


def parse_month(value: str | None) -> date | None:
    """
    Parse a string in YYYY-MM format into a date object with day=1. Returns None if invalid.
    """
    return datetime.strptime(value, "%Y-%m").date().replace(day=1) if value else None


def normalize_symbols(symbols: Sequence[str] | None) -> FrozenSet[Symbol] | None:
    """
    Normalize symbols into uppercase Symbol values. Returns None if symbols is None/empty.
    """
    return frozenset(Symbol(s.upper()) for s in symbols) if symbols else None


def build_key_filter(
    symbols: Sequence[str] | None, start: str | None, end: str | None
) -> KeyFilter:
    """
    Build and return a KeyFilter based on raw inputs for symbols and date range.
    """
    return KeyFilter(
        symbols=normalize_symbols(symbols),
        start_month=parse_month(start),
        end_month=parse_month(end),
    )


def key_symbol(prefix: str, key: str) -> Symbol | None:
    """
    Extract the symbol from the S3 key given a known prefix.
    """
    if not key.startswith(prefix):
        return None

    rest = key[len(prefix) :]
    parts = rest.split("/", 1)

    if not parts:
        return None

    sym = parts[0]

    return Symbol(sym) if sym else None


def key_month(key: str) -> date | None:
    """
    Extract and return the month from the basename of the key (YYYY-MM).
    """
    if not is_trade_zip_key(key):
        return None

    base = os.path.basename(key)
    name_no_ext = base[:-4]  # strip ".zip"
    segments = name_no_ext.split("-")

    if len(segments) < 3:
        return None

    date_str = f"{segments[-2]}-{segments[-1]}"

    try:
        return datetime.strptime(date_str, "%Y-%m").date().replace(day=1)
    except ValueError:
        return None


def is_trade_zip_key(key: str) -> bool:
    """
    Check if the key is a valid trade archive (ends with ".zip" and not ".CHECKSUM.zip").
    """
    base = os.path.basename(key)

    return base.endswith(".zip") and not base.endswith(".CHECKSUM.zip")


def matches_filter(key: str, prefix: str, flt: KeyFilter) -> bool:
    """
    Check if the key matches the criteria specified in the KeyFilter.
    """
    month = key_month(key)

    if month is None:
        return False

    if flt.symbols is not None:
        sym = key_symbol(prefix, key)

        if sym is None or sym not in flt.symbols:
            return False

    if flt.start_month is not None and month < flt.start_month:
        return False

    if flt.end_month is not None and month > flt.end_month:
        return False

    return True


def filter_trade_keys(keys: Iterable[str], prefix: str, flt: KeyFilter) -> list:
    """
    Filter and return the S3 keys that match the given filter criteria.
    """
    return sorted([key for key in keys if matches_filter(key=key, prefix=prefix, flt=flt)], key=str)
