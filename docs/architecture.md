# Architecture

## Overview

matplotlib の Figure を OriginLab グラフに変換するモノレポ。
Origin のインストール状況に応じてローカル実行（core）とリモート実行（remote → server）を自動切替する。

## Entry Points

- `client/matplotlib_to_originlab/__init__.py` — `mto.run(fig, ax)` ユーザー API。ローカル/リモートを自動選択
- `server/matplotlib_to_originlab_server/app.py` — FastAPI アプリ起動点（Origin ノード側）
- `server/matplotlib_to_originlab_server/app.py:main` — CLI エントリーポイント (`matplotlib-to-originlab-server` コマンド)

## Directory Structure

| ディレクトリ / ファイル | 役割 |
|---|---|
| `client/` | ユーザー向けクライアント（全OS）。core か remote を自動選択 |
| `core/` | ローカル実行エンジン（Windows + OriginLab 必須）。originpro / win32com 使用 |
| `remote/` | HTTP クライアント。server に対して job を投入・結果取得 |
| `server/` | Origin 実行ノード（FastAPI）。job キューを管理し Worker が Origin を操作 |
| `tests/` | 統合テスト |
| `docs/` | アーキテクチャ・仕様・ファイルマップ等のドキュメント |

## Data Flow

```
[User Code]
    ↓ mto.run(fig, ax)
client
    ├─ origin_available() == True  → core  (ローカル、Windows + Origin)
    └─ origin_available() == False → remote (HTTP クライアント)
                                        ↓ POST /job
                                      server (FastAPI)
                                        ↓
                                      Job DB (SQLite)
                                        ↓
                                      Worker thread
                                        ↓
                                      OriginLab
```

## Key Dependencies

| ライブラリ / モジュール | 用途 |
|---|---|
| `originpro` | OriginLab Python API（core, Windows のみ） |
| `pywin32` | COM オートメーション（core, Windows のみ） |
| `fastapi` / `uvicorn` | HTTP サーバー（server） |
| `httpx` | HTTP クライアント（remote） |
| `matplotlib` | Figure 入力形式（client, core） |

## Platform Notes

- Windows のみ: `core/`（originpro + win32com）、`server/`
- クロスプラットフォーム: `client/`、`remote/`
