import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import List, Optional, Union

import boto3
from botocore import UNSIGNED
from botocore.config import Config

try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(iterable, **kwargs):
        return iterable


class DownloadError(Exception):
    """Raised when a file download repeatedly fails."""


class BinanceTradeDownloader:
    """
    Downloader for Binance spot-trade .zip files stored in the public S3 bucket.

    Features:
      - Filter by trading symbol(s)
      - Filter by start/end month (YYYY-MM)
      - Retry logic with exponential backoff
      - Overwrite or skip existing files
      - Dry-run mode
      - Progress reporting via tqdm
    """

    def __init__(
        self,
        bucket_name: str = "data.binance.vision",
        prefix: str = "data/spot/monthly/trades/",
        region: str = "ap-northeast-1",
        max_workers: Optional[int] = None,
        s3_client=None,
        log_level: str = "INFO",
    ):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.region = region
        self.max_workers = max_workers or os.cpu_count() or 4

        # Configure logger
        self.logger = logging.getLogger(self.__class__.__name__)
        # Prevent double logging if root logger is configured
        self.logger.propagate = False
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # S3 client
        if s3_client is None:
            self._s3 = boto3.client(
                "s3",
                region_name=self.region,
                config=Config(signature_version=UNSIGNED),
            )
        else:
            self._s3 = s3_client

    def list_files(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[str]:
        """
        List all .zip trade files, with optional filtering.

        :param symbols: single symbol or list of symbols (e.g. "BTCUSDT")
        :param start: include files from this month (YYYY-MM)
        :param end: include files up to this month (YYYY-MM)
        :return: list of S3 keys
        """
        symbol_list = None
        if symbols:
            symbol_list = [symbols] if isinstance(symbols, str) else symbols
            symbol_list = [s.upper() for s in symbol_list]

        start_date: Optional[date] = None
        end_date: Optional[date] = None
        if start:
            start_date = (
                datetime.strptime(start, "%Y-%m").date().replace(day=1)
            )
        if end:
            end_date = datetime.strptime(end, "%Y-%m").date().replace(day=1)

        paginator = self._s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)
        result: List[str] = []

        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".zip") or key.endswith(".CHECKSUM.zip"):
                    continue

                # Filter by symbol
                if symbol_list:
                    parts = key[len(self.prefix) :].split("/", 1)
                    if not parts or parts[0] not in symbol_list:
                        continue

                # Filter by date
                basename = os.path.basename(key)
                name_no_ext = basename[:-4]
                segments = name_no_ext.split("-")
                if len(segments) < 3:
                    continue
                date_str = segments[-2] + "-" + segments[-1]
                try:
                    file_date = (
                        datetime.strptime(date_str, "%Y-%m")
                        .date()
                        .replace(day=1)
                    )
                except ValueError:
                    self.logger.debug(
                        f"Skipping unparsable date in key: {key}"
                    )
                    continue
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue

                result.append(key)

        return sorted(result)

    def download(
        self,
        key: str,
        target_dir: str,
        overwrite: bool = False,
        retries: int = 3,
        dry_run: bool = False,
    ) -> None:
        """
        Download a single file by S3 key into target_dir (preserving subpaths).

        :raises DownloadError: if retries are exhausted
        """
        rel_path = key[len(self.prefix) :]
        local_path = os.path.join(target_dir, rel_path)

        if dry_run:
            self.logger.info(
                f"[dry-run] Would download: {key} -> {local_path}"
            )
            return

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if os.path.exists(local_path) and not overwrite:
            self.logger.debug(f"Skipping existing: {local_path}")
            return

        attempt = 0
        while attempt < retries:
            try:
                self._s3.download_file(self.bucket_name, key, local_path)
                return
            except Exception as e:
                attempt += 1
                wait = 2**attempt
                self.logger.warning(
                    f"Error downloading {key} (attempt {attempt}/{retries}): {e}. Retrying in {wait}s"
                )
                time.sleep(wait)

        raise DownloadError(
            f"Failed to download {key} after {retries} attempts"
        )

    def download_all(
        self,
        target_dir: str,
        symbols: Optional[Union[str, List[str]]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        overwrite: bool = False,
        dry_run: bool = False,
    ) -> None:
        """
        Download all matching files in parallel or preview with dry-run.
        """
        keys = self.list_files(symbols=symbols, start=start, end=end)
        total = len(keys)
        self.logger.info(f"Found {total} files to process.")

        if dry_run:
            for key in keys:
                rel_path = key[len(self.prefix) :]
                local_path = os.path.join(target_dir, rel_path)
                self.logger.info(
                    f"[dry-run] Would download: {key} -> {local_path}"
                )
            return

        os.makedirs(target_dir, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.download, key, target_dir, overwrite): key
                for key in keys
            }
            for fut in tqdm(
                as_completed(futures),
                total=total,
                desc="Downloading",
                unit="file",
            ):
                key = futures[fut]
                try:
                    fut.result()
                    self.logger.info(f"Downloaded: {key}")
                except Exception as e:
                    self.logger.error(f"Failed: {key}: {e}")
