from unittest.mock import Mock

import pytest
from botocore import UNSIGNED

import binance_s3_trades.downloader as dl
from binance_s3_trades.downloader import DownloadError


def test_create_s3_client_uses_unsigned_and_pool_size(monkeypatch):
    client_mock = Mock()
    boto3_client = Mock(return_value=client_mock)
    monkeypatch.setattr(dl.boto3, "client", boto3_client)

    got = dl.create_s3_client(region="ap-northeast-1", max_workers=7)
    assert got is client_mock

    boto3_client.assert_called_once()
    _, kwargs = boto3_client.call_args
    assert kwargs["region_name"] == "ap-northeast-1"
    cfg = kwargs["config"]
    # Config exposes these attributes in botocore
    assert cfg.signature_version == UNSIGNED
    assert cfg.max_pool_connections == 7


def test_iter_s3_keys_from_pages_yields_only_string_keys():
    pages = [
        {"Contents": [{"Key": "a"}, {"Key": 123}, {"Key": None}, {"Key": "b"}]},
        {"Contents": "not-a-list"},
        {"Contents": [{"NoKey": True}, "bad", {"Key": "c"}]},
        {},
    ]
    assert list(dl.iter_s3_keys_from_pages(pages)) == ["a", "b", "c"]


def test_list_files_integrates_paginator_and_filters(fake_s3_client, s3_prefix: str, caplog):
    # Use the real core filtering (no AWS calls).
    caplog.set_level("INFO")

    out = dl.list_files(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        symbols=["BTCUSDT"],
        start="2024-02",
        end="2024-03",
    )

    assert out == [f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-02.zip"]
    # The fake paginator should have been used with provided Bucket/Prefix.
    assert fake_s3_client._paginator.calls
    _, kwargs = fake_s3_client._paginator.calls[0]
    assert kwargs["Bucket"] == "bucket"
    assert kwargs["Prefix"] == s3_prefix
    assert "Found 1 matching files" in caplog.text


def test_download_file_dry_run_does_not_create_dirs_or_download(
    tmp_path, fake_s3_client, s3_prefix: str
):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    target = tmp_path / "out"

    dl.download_file(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        key=key,
        target_dir=str(target),
        overwrite=False,
        retries=3,
        dry_run=True,
        sleeper=lambda _: (_ for _ in ()).throw(AssertionError("sleeper should not be called")),
    )

    assert fake_s3_client.download_calls == []
    assert not target.exists()


def test_download_file_skips_existing_when_not_overwriting(
    tmp_path, fake_s3_client, s3_prefix: str
):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    target = tmp_path / "out"
    local = target / "BTCUSDT" / "BTCUSDT-trades-2024-01.zip"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"already here")

    dl.download_file(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        key=key,
        target_dir=str(target),
        overwrite=False,
        retries=3,
        dry_run=False,
        sleeper=lambda _: None,
    )

    assert fake_s3_client.download_calls == []


def test_download_file_retries_then_succeeds(tmp_path, fake_s3_client, s3_prefix: str):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    target = tmp_path / "out"

    fake_s3_client.set_download_side_effects([RuntimeError("boom1"), RuntimeError("boom2"), None])

    sleeps: list[float] = []

    dl.download_file(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        key=key,
        target_dir=str(target),
        overwrite=True,
        retries=3,
        dry_run=False,
        sleeper=sleeps.append,
    )

    # Two failures -> two sleeps with exponential backoff (2, 4)
    assert sleeps == [2.0, 4.0]
    assert len(fake_s3_client.download_calls) == 3

    # Directory structure should exist (file creation is done by boto3, which we mock)
    expected_dir = target / "BTCUSDT"
    assert expected_dir.exists()
    assert expected_dir.is_dir()


def test_download_file_exhausts_retries_raises_download_error(
    tmp_path, fake_s3_client, s3_prefix: str
):
    key = f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"
    target = tmp_path / "out"

    fake_s3_client.set_download_side_effects([RuntimeError("x")] * 10)

    sleeps: list[float] = []

    with pytest.raises(DownloadError):
        dl.download_file(
            s3_client=fake_s3_client,
            bucket_name="bucket",
            prefix=s3_prefix,
            key=key,
            target_dir=str(target),
            overwrite=True,
            retries=3,
            dry_run=False,
            sleeper=sleeps.append,
        )

    # Current behavior sleeps after each failed attempt, including the last one.
    assert sleeps == [2.0, 4.0, 8.0]
    assert len(fake_s3_client.download_calls) == 3


def test_download_all_dry_run_does_not_create_target_dir(tmp_path, fake_s3_client, s3_prefix: str):
    target = tmp_path / "out"
    dl.download_all(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        keys=[f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"],
        target_dir=str(target),
        dry_run=True,
    )
    assert not target.exists()


def test_download_all_dispatches_downloads_and_swallows_exceptions(
    monkeypatch, tmp_path, fake_s3_client, s3_prefix: str, caplog
):
    caplog.set_level("INFO")
    target = tmp_path / "out"
    keys = [
        f"{s3_prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip",
        f"{s3_prefix}ETHUSDT/ETHUSDT-trades-2024-01.zip",
    ]

    calls: list[str] = []

    def fake_download_file(**kwargs):
        calls.append(kwargs["key"])
        if "ETHUSDT" in kwargs["key"]:
            raise RuntimeError("worker failed")

    monkeypatch.setattr(dl, "download_file", fake_download_file)

    dl.download_all(
        s3_client=fake_s3_client,
        bucket_name="bucket",
        prefix=s3_prefix,
        keys=keys,
        target_dir=str(target),
        max_workers=1,  # deterministic
        dry_run=False,
    )

    assert target.exists()
    assert calls == keys
    assert "All downloads completed" in caplog.text
