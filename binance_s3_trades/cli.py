from typing import List, Optional

import typer

from .downloader import BinanceTradeDownloader, DownloadError

app = typer.Typer(help="List & download Binance spot-trade archives from S3")


def _get_downloader(log_level: str):
    return BinanceTradeDownloader(log_level=log_level)


@app.command()
def list(
    symbol: Optional[List[str]] = typer.Option(
        None, "-s", "--symbol", help="Trading symbol(s), e.g. BTCUSDT"
    ),
    start: Optional[str] = typer.Option(None, help="Start month (YYYY-MM)"),
    end: Optional[str] = typer.Option(None, help="End   month (YYYY-MM)"),
    log_level: str = typer.Option("INFO", help="Logging level"),
):
    """
    List all matching .zip keys on S3.
    """
    dl = _get_downloader(log_level)
    keys = dl.list_files(symbols=symbol, start=start, end=end)
    for k in keys:
        typer.echo(k)
    typer.echo(f"\nTotal: {len(keys)}")


@app.command()
def download(
    out_dir: str = typer.Argument(".", help="Target directory for downloads"),
    symbol: Optional[List[str]] = typer.Option(
        None, "-s", "--symbol", help="Trading symbol(s), e.g. BTCUSDT"
    ),
    start: Optional[str] = typer.Option(None, help="Start month (YYYY-MM)"),
    end: Optional[str] = typer.Option(None, help="End   month (YYYY-MM)"),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Redownload existing"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would download"
    ),
    log_level: str = typer.Option("INFO", help="Logging level"),
):
    """
    Download matching .zip files in parallel.
    """
    dl = _get_downloader(log_level)
    try:
        dl.download_all(
            target_dir=out_dir,
            symbols=symbol,
            start=start,
            end=end,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except DownloadError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
