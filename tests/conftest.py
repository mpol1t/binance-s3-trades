from typing import Any, Iterable

import pytest


@pytest.fixture()
def s3_prefix() -> str:
    return "data/spot/monthly/trades/"


@pytest.fixture()
def sample_keys(s3_prefix: str) -> list[str]:
    # Two symbols, multiple months, plus some junk keys.
    return [
        f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip",
        f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-02.zip",
        f"{s3_prefix}ETHUSDT/ETHUSDT-trades-2024-01.zip",
        f"{s3_prefix}ETHUSDT/ETHUSDT-trades-2024-03.zip",
        f"{s3_prefix}ETHUSDT/ETHUSDT-trades-2024-03.CHECKSUM.zip",  # excluded
        f"{s3_prefix}BTCUSDT/readme.txt",  # excluded
        "other/prefix/BTCUSDT/BTCUSDT-trades-2024-01.zip",  # valid zip but wrong prefix
    ]


class FakePaginator:
    def __init__(self, pages: Iterable[dict[str, Any]]):
        self._pages = list(pages)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def paginate(self, **kwargs: Any):
        self.calls.append(("paginate", dict(kwargs)))
        return iter(self._pages)


class FakeS3Client:
    def __init__(self, pages: Iterable[dict[str, Any]]):
        self._paginator = FakePaginator(pages)
        self.download_calls: list[tuple[str, str, str]] = []
        self._download_side_effects: list[Exception | None] = []

    def get_paginator(self, name: str):
        assert name == "list_objects_v2"
        return self._paginator

    def set_download_side_effects(self, effects: list[Exception | None]) -> None:
        self._download_side_effects = list(effects)

    def download_file(self, bucket: str, key: str, filename: str) -> None:
        self.download_calls.append((bucket, key, filename))
        if self._download_side_effects:
            effect = self._download_side_effects.pop(0)
            if effect is not None:
                raise effect


@pytest.fixture()
def fake_s3_pages(sample_keys: list[str]) -> list[dict[str, Any]]:
    # Simulate boto paginator pages: only some entries are well-formed.
    return [
        {"Contents": [{"Key": sample_keys[0]}, {"Key": sample_keys[1]}]},
        {"Contents": [{"Key": sample_keys[2]}, {"Key": sample_keys[3]}]},
        {"Contents": "not-a-list"},  # ignored
        {"NoContentsHere": True},  # ignored
        {"Contents": [{"Key": None}, {"Key": 123}, "bad-obj", {"Key": sample_keys[4]}]},
    ]


@pytest.fixture()
def fake_s3_client(fake_s3_pages: list[dict[str, Any]]) -> FakeS3Client:
    return FakeS3Client(fake_s3_pages)
