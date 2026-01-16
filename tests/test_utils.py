import os

from binance_s3_trades.utils import local_path_for_key


def test_local_path_for_key_strips_prefix_when_present(tmp_path):
    prefix = "data/spot/monthly/trades/"
    key = f"{prefix}BTCUSDT/BTCUSDT-trades-2024-01.zip"

    out = local_path_for_key(key=key, prefix=prefix, target_dir=str(tmp_path))

    assert out == os.path.join(str(tmp_path), "BTCUSDT", "BTCUSDT-trades-2024-01.zip")


def test_local_path_for_key_keeps_key_when_prefix_not_present(tmp_path):
    key = "other/prefix/BTCUSDT/file.zip"

    out = local_path_for_key(
        key=key,
        prefix="data/spot/monthly/trades/",
        target_dir=str(tmp_path),
    )

    assert out == os.path.join(str(tmp_path), key)
