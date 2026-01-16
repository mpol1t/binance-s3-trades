format: ;poetry run ruff check --select I,F401 --fix . && poetry run black .
lint:   ;poetry run ruff check .
type:   ;poetry run mypy src/
test:   ;poetry run pytest --cov=src/
all:    format lint type test
