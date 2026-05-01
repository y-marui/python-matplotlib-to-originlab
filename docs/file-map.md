# File Map

_最終更新: 2026-05-01_

## client

| ファイル | 役割 | 主な依存先 |
|---|---|---|
| `client/matplotlib_to_originlab/__init__.py` | `run()` API。origin_available() でバックエンド選択 | `core`, `remote` |

## remote

| ファイル | 役割 | 主な依存先 |
|---|---|---|
| `remote/matplotlib_to_originlab_remote/__init__.py` | `configure()` / HTTP job 投入・結果取得 | `httpx` |

## server

| ファイル | 役割 | 主な依存先 |
|---|---|---|
| `server/matplotlib_to_originlab_server/app.py` | FastAPI アプリ・CLI エントリーポイント | `fastapi`, `db.py`, `worker.py` |
| `server/matplotlib_to_originlab_server/db.py` | SQLite job DB（CRUD） | `sqlite3` |

## core

| ファイル | 役割 | 主な依存先 |
|---|---|---|
| `core/matplotlib_to_originlab_core/` | OriginLab 操作（線・散布図・棒グラフ等） | `originpro`, `win32com` |
