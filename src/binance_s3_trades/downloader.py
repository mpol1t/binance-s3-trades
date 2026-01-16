import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable

import boto3
from botocore import UNSIGNED
from botocore.config import Config

from binance_s3_trades.core import build_key_filter, filter_trade_keys
from binance_s3_trades.utils import local_path_for_key

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when a file download repeatedly fails."""


Sleeper = Callable[[float], None]


def create_s3_client(region: str, max_workers: int) -> Any:
    """
    Create an unsigned S3 client with an HTTP pool large enough for concurrency.
    """
    return boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version=UNSIGNED, max_pool_connections=max_workers),
    )


def iter_s3_keys_from_pages(pages: Iterable[dict[str, Any]]) -> Iterable[str]:
    """
    Extract Key values from paginator pages.

    This isolates boto3's loosely-typed paginator output at the boundary.
    """
    for page in pages:
        contents = page.get("Contents", [])

        if not isinstance(contents, list):
            continue

        for obj in contents:
            if not isinstance(obj, dict):
                continue

            key = obj.get("Key")

            if isinstance(key, str):
                yield key


def list_files(
    s3_client: Any,
    bucket_name: str,
    prefix: str,
    symbols: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """
    List and filter matching trade .zip keys from S3.
    """
    flt = build_key_filter(symbols=symbols, start=start, end=end)

    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    all_keys = iter_s3_keys_from_pages(pages)
    filtered = filter_trade_keys(keys=all_keys, prefix=prefix, flt=flt)

    result = [str(k) for k in filtered]

    logger.info("Found %d matching files", len(result))

    return result


def download_file(
    s3_client: Any,
    bucket_name: str,
    prefix: str,
    key: str,
    target_dir: str,
    overwrite: bool,
    retries: int,
    dry_run: bool,
    sleeper: Sleeper,
) -> None:
    """
    Download a single S3 key into target_dir, preserving relative layout.
    """
    local_path = local_path_for_key(key=key, prefix=prefix, target_dir=target_dir)

    if dry_run:
        logger.info("Dry-run: %s -> %s", key, local_path)
        return

    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    if os.path.exists(local_path) and not overwrite:
        logger.debug("Skipping existing file: %s", local_path)
        return

    attempt = 0

    while attempt < retries:
        try:
            logger.debug("Downloading %s (attempt %d)", key, attempt + 1)

            s3_client.download_file(bucket_name, key, local_path)

            logger.info("Downloaded %s", key)

            return
        except Exception:
            attempt += 1
            wait = 1 << attempt

            logger.warning(
                "Download failed (%s), retry %d/%d in %ds",
                key,
                attempt,
                retries,
                wait,
            )

            sleeper(float(wait))

    logger.error("Giving up on %s after %d attempts", key, retries)

    raise DownloadError(f"Failed to download {key} after {retries} attempts")


def download_all(
    s3_client: Any,
    bucket_name: str,
    prefix: str,
    keys: list[str],
    target_dir: str,
    overwrite: bool = False,
    dry_run: bool = False,
    max_workers: int = 4,
    retries: int = 3,
    sleeper: Sleeper = time.sleep,
) -> None:
    """
    Download many S3 keys in parallel.
    """
    if dry_run:
        logger.info("Dry-run: skipping download of %d files", len(keys))
        return

    logger.info(
        "Starting download of %d files using %d workers",
        len(keys),
        max_workers,
    )

    os.makedirs(target_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                download_file,
                s3_client=s3_client,
                bucket_name=bucket_name,
                prefix=prefix,
                key=key,
                target_dir=target_dir,
                overwrite=overwrite,
                retries=retries,
                dry_run=dry_run,
                sleeper=sleeper,
            ): key
            for key in keys
        }

        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception:
                logger.exception("Download task failed")

    logger.info("All downloads completed")
