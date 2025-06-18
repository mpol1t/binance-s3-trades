# Contributing to binance-s3-trades

Thank you for considering contributing to **binance-s3-trades**! We welcome bug reports, feature requests, and pull requests.

---

## Code of Conduct

This project is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms. Please report unacceptable behavior to michal.polit@monadic.eu.

---

## Getting Started

1. **Fork** the repository on GitHub:
   https://github.com/mpolit/binance-s3-trades
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/yourusername/binance-s3-trades.git
   cd binance-s3-trades
   ```
3. **Install** dependencies and activate virtualenv:
   ```bash
   poetry install
   poetry shell   # optional
   ```

---

## Project Structure

- `src/binance_s3_trades/` – core library
  - `downloader.py` – S3 listing & download logic
  - `cli.py`        – Typer-powered command-line interface
- `tests/`           – unit tests (uses pytest & mocks)
- `.github/`         – GitHub workflows, issue & PR templates
- `pyproject.toml`   – project metadata & dependencies

---

## Reporting Bugs

Before filing a bug, please:

1. Search existing issues: https://github.com/mpolit/binance-s3-trades/issues
2. Verify you’re running the latest `main` branch or latest PyPI release.
3. Include in your report:
   - A clear, descriptive title.
   - Steps to reproduce.
   - Expected vs. actual behavior.
   - Python version, OS, and installed package versions (`poetry show`).

---

## Suggesting Enhancements

1. Check if a similar feature request exists; if not, open a new issue.
2. Describe your use case and rationale.
3. Optionally, sketch out a short example of how the API might look.

---

## Your First Code Contribution

Look for issues labeled **help wanted** or **good first issue**:

- https://github.com/mpolit/binance-s3-trades/labels/help%20wanted
- https://github.com/mpolit/binance-s3-trades/labels/good%20first%20issue

---

## Pull Request Guidelines

1. Fork, create a feature branch, and commit logically‐grouped changes.
2. Base your branch off `main`.
3. Ensure all tests pass:
   ```bash
   poetry run pytest
   ```
4. Include or update unit tests for new functionality.
5. Adhere to PEP 8 and project style (`flake8`).
6. Don’t include issue numbers in the PR title—reference them in the description.
7. Provide screenshots or logs if relevant.

---

## Style Guides

### Commit Messages

- Use the imperative mood: “Add feature”, not “Added feature”.
- Keep the first line ≤ 72 characters.
- Separate subject from body with a blank line.
- Reference issues/PRs: “Fixes #123”.

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- Use docstrings for all public functions and classes.
- Type‐annotate function signatures.

---

## Issue & PR Labels

We use these labels to track work:

- **bug** – a confirmed defect
- **enhancement** – new feature requests
- **help wanted** – contributions welcome
- **good first issue** – suitable for newcomers
- **question** – usage or design questions

---

## Thank You!

Your contributions make this library better for everyone. We look forward to your bug reports, ideas, and pull requests!
