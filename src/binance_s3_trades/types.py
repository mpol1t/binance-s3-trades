from datetime import date
from typing import FrozenSet, NamedTuple

Symbol = str
S3Key = str


class KeyFilter(NamedTuple):
    symbols: FrozenSet[Symbol] | None
    start_month: date | None
    end_month: date | None
