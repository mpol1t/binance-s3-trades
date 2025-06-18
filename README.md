# binance-s3-trades
Seamlessly list and download Binance spot-trade `.zip` archives from Binance’s public S3 bucket.

## Installation

**From PyPI**
```bash
pip install binance-s3-trades
```

**From source**
```bash
git clone https://github.com/mpolit/binance-s3-trades.git
cd binance-s3-trades
poetry install
```

## Usage

### Python API
```python
from binance_s3_trades import BinanceTradeDownloader

dl = BinanceTradeDownloader(
    max_workers=4,
    log_level="INFO"
)

# List all BTCUSDT trades for Jan–Mar 2023
keys = dl.list_files(symbols="BTCUSDT", start="2023-01", end="2023-03")
print(keys)

# Dry-run download into ./data
dl.download_all(
    target_dir="./data",
    symbols="BTCUSDT",
    start="2023-01",
    end="2023-03",
    dry_run=True
)
```

### Command-Line Interface

After installation, use the `binance-s3-trades` command:

```bash
# List matching files
binance-s3-trades list \
  --symbol BTCUSDT \
  --start 2023-01 \
  --end   2023-03

# Download (with overwriting or dry-run)
binance-s3-trades download ./data \
  --symbol BTCUSDT \
  --start 2023-01 \
  --dry-run
```

Run `binance-s3-trades --help` for full options.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and our code of conduct.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
