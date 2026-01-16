# binance-s3-trades

Seamlessly list and download Binance spot trade `.zip` archives from Binance’s public S3 bucket.

This project provides:
- a Python API for listing and downloading trade archives
- a command-line interface built with Typer
- parallel downloads using boto3 with unsigned S3 access

---

## Installation

### From PyPI

```bash
pip install binance-s3-trades
```
### From source

```bash
git clone https://github.com/mpolit/binance-s3-trades.git
cd binance-s3-trades
poetry install
```

---

## Python API

### Listing available trade archives

```python
from binance_s3_trades.downloader import create_s3_client, list_files

s3 = create_s3_client(
    region="ap-northeast-1",
    max_workers=4,
)

keys = list_files(
    s3_client=s3,
    bucket_name="data.binance.vision",
    prefix="data/spot/monthly/trades/",
    symbols=["BTCUSDT"],
    start="2023-01",
    end="2023-03",
)

print(keys)
```

---

### Downloading trade archives


```python3
from binance_s3_trades.downloader import (
    create_s3_client,
    list_files,
    download_all,
)

s3 = create_s3_client(
    region="ap-northeast-1",
    max_workers=4,
)

keys = list_files(
    s3_client=s3,
    bucket_name="data.binance.vision",
    prefix="data/spot/monthly/trades/",
    symbols=["BTCUSDT"],
    start="2023-01",
    end="2023-03",
)

download_all(
    s3_client=s3,
    bucket_name="data.binance.vision",
    prefix="data/spot/monthly/trades/",
    keys=keys,
    target_dir="./data",
    overwrite=False,
    dry_run=False,
    max_workers=4,
)
```

---

## Command-Line Interface

After installation, the binance-s3-trades command is available.

### List matching files

```bash
binance-s3-trades list \
  --symbol BTCUSDT \
  --start 2023-01 \
  --end 2023-03
```

### Download files

```bash
binance-s3-trades download ./data \
  --symbol BTCUSDT \
  --start 2023-01 \
  --overwrite
```

### Dry-run mode

```bash
binance-s3-trades download ./data \
  --symbol BTCUSDT \
  --start 2023-01 \
  --dry-run
```

Run the following for full options:

```bash
binance-s3-trades --help
```

---

## Contributing

Contributions are welcome.
Please open an issue or pull request on GitHub.

---

## License

This project is licensed under the MIT License.
See the LICENSE file for details.
