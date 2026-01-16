import logging

from typer import Argument, Exit, Option, Typer, colors, echo, secho

from binance_s3_trades.downloader import create_s3_client, download_all, list_files
from binance_s3_trades.logging import setup_logging
from binance_s3_trades.utils import local_path_for_key

logger = logging.getLogger(__name__)

app = Typer(help="List & download Binance spot-trade archives from S3")


DEFAULT_BUCKET = "data.binance.vision"
DEFAULT_PREFIX = "data/spot/monthly/trades/"
DEFAULT_REGION = "ap-northeast-1"


@app.command("list")
def list_keys(
    symbol: list[str] | None = Option(
        None, "-s", "--symbol", help="Trading symbol(s), e.g. BTCUSDT"
    ),
    start: str | None = Option(None, help="Start month (YYYY-MM)"),
    end: str | None = Option(None, help="End month (YYYY-MM)"),
    workers: int = Option(
        1, "--workers", "-w", help="Number of parallel downloads (also sizes S3 HTTP pool)"
    ),
) -> None:
    """List all matching .zip keys on S3."""
    keys = list_files(
        s3_client=create_s3_client(region=DEFAULT_REGION, max_workers=workers),
        bucket_name=DEFAULT_BUCKET,
        prefix=DEFAULT_PREFIX,
        symbols=symbol,
        start=start,
        end=end,
    )

    for k in keys:
        echo(k)

    echo(f"\nTotal: {len(keys)}")


@app.command("download")
def download(
    out_dir: str = Argument(".", help="Target directory for downloads"),
    symbols: list[str] | None = Option(
        None, "-s", "--symbol", help="Trading symbol(s), e.g. BTCUSDT"
    ),
    start: str | None = Option(None, help="Start month (YYYY-MM). Defaults to 1970-01."),
    end: str | None = Option(None, help="End month (YYYY-MM)"),
    overwrite: bool = Option(False, "--overwrite", help="Redownload existing"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would download"),
    workers: int = Option(1, "--workers", "-w", help="Number of parallel downloads"),
) -> None:
    """Download matching .zip files in parallel."""
    s3_client = create_s3_client(region=DEFAULT_REGION, max_workers=workers)
    start_month = start or "1970-01"

    keys = list_files(
        s3_client=s3_client,
        bucket_name=DEFAULT_BUCKET,
        prefix=DEFAULT_PREFIX,
        symbols=symbols,
        start=start_month,
        end=end,
    )

    echo(f"Found {len(keys)} files to process.")
    echo(f"Using {workers} worker threads.")

    if dry_run:
        for key in keys:
            local_path = local_path_for_key(key=key, prefix=DEFAULT_PREFIX, target_dir=out_dir)
            echo(f"[dry-run] Would download: {key} -> {local_path}")
        return

    try:
        download_all(
            s3_client=s3_client,
            bucket_name=DEFAULT_BUCKET,
            prefix=DEFAULT_PREFIX,
            keys=keys,
            target_dir=out_dir,
            overwrite=overwrite,
            dry_run=dry_run,
            max_workers=workers,
        )
    except Exception as e:
        logger.exception("Download command failed")
        secho(f"Error: {e}", fg=colors.RED)

        raise Exit(code=1) from e


@app.callback()
def main(
    log_level: str = Option("INFO", "--log-level", help="DEBUG|INFO|WARNING|ERROR"),
) -> None:
    setup_logging(log_level)
    logger.debug("Logging initialized (level=%s)", log_level)
