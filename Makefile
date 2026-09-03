.PHONY: install lint format type test all update-charter

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy remote/matplotlib_to_originlab_remote server/matplotlib_to_originlab_server/app.py server/matplotlib_to_originlab_server/db.py

test:
	uv run pytest remote/tests/ server/tests/

all: lint type test

update-charter: ## dev-charter を最新版に更新
	curl -fsSL https://raw.githubusercontent.com/y-marui/dev-charter/main/scripts/install.sh | CHARTER_UPDATE_ONLY=1 bash
