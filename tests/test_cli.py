from typer.testing import CliRunner

import binance_s3_trades.cli as cli

runner = CliRunner()


def test_cli_list_prints_keys_and_total(monkeypatch):
    fake_keys = [
        "data/spot/monthly/trades/BTCUSDT/BTCUSDT-trades-2024-01.zip",
        "data/spot/monthly/trades/BTCUSDT/BTCUSDT-trades-2024-02.zip",
    ]

    # Patch where used: cli.create_s3_client and cli.list_files
    monkeypatch.setattr(cli, "create_s3_client", lambda region, max_workers: object())
    monkeypatch.setattr(cli, "list_files", lambda **kwargs: list(fake_keys))

    result = runner.invoke(
        cli.app,
        ["list", "--symbol", "BTCUSDT", "--start", "2024-01", "--end", "2024-02", "--workers", "3"],
    )

    assert result.exit_code == 0
    # keys printed one per line + "Total: N"
    for k in fake_keys:
        assert k in result.stdout
    assert "Total: 2" in result.stdout


def test_cli_download_dry_run_prints_plan_and_does_not_call_download_all(monkeypatch, tmp_path):
    keys = [
        "data/spot/monthly/trades/BTCUSDT/BTCUSDT-trades-2024-01.zip",
        "data/spot/monthly/trades/ETHUSDT/ETHUSDT-trades-2024-01.zip",
    ]

    monkeypatch.setattr(cli, "create_s3_client", lambda region, max_workers: object())
    monkeypatch.setattr(cli, "list_files", lambda **kwargs: list(keys))

    called = {"download_all": False}

    def fail_if_called(**kwargs):
        called["download_all"] = True
        raise AssertionError("download_all must not be called in --dry-run mode")

    monkeypatch.setattr(cli, "download_all", fail_if_called)

    result = runner.invoke(
        cli.app,
        ["download", str(tmp_path), "--dry-run", "--workers", "2"],
    )

    assert result.exit_code == 0
    assert "Found 2 files to process." in result.stdout
    assert "Using 2 worker threads." in result.stdout
    assert called["download_all"] is False

    # Should print mapping for each key
    for k in keys:
        assert f"[dry-run] Would download: {k} -> " in result.stdout


def test_cli_download_start_defaults_to_1970_01(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli, "create_s3_client", lambda region, max_workers: object())

    def fake_list_files(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(cli, "list_files", fake_list_files)
    monkeypatch.setattr(cli, "download_all", lambda **kwargs: None)

    result = runner.invoke(cli.app, ["download", str(tmp_path), "--workers", "1", "--dry-run"])
    assert result.exit_code == 0

    # start should be defaulted in cli.download when omitted
    assert captured["start"] == "1970-01"


def test_cli_download_failure_exits_1_and_shows_error(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "create_s3_client", lambda region, max_workers: object())
    monkeypatch.setattr(cli, "list_files", lambda **kwargs: ["k1.zip"])

    def boom(**kwargs):
        raise RuntimeError("nope")

    monkeypatch.setattr(cli, "download_all", boom)

    result = runner.invoke(cli.app, ["download", str(tmp_path)])

    assert result.exit_code == 1
    # stable substring; don't assert full formatting/colors
    assert "Error:" in result.stdout
    assert "nope" in result.stdout
