# AI_CONTEXT — matplotlib-to-originlab

## Reference Order

AI はタスク開始時に以下の順で参照する:

1. `README-jp.md`（概要・セットアップ）
2. `DEVELOPING.md`（ビルド・実装規約・命名規則）※未作成の場合は AI_CONTEXT.md の Project-Specific Rules を参照

必要に応じて以下を参照する（順不同）:
- `CONTRIBUTING.md`（PR・Issue ルール）
- `docs/architecture.md`（モジュール・コンポーネント構造）
- `docs/file-map.md`（ファイルレベルの依存関係 ※情報が足りない・古い場合は適宜探索し、追記・更新する）
- `docs/specification.md`（機能仕様・データフロー）
- `docs/ui-design.md`（UI 設計・コンポーネント仕様）

---

## Project Overview

**Purpose:** matplotlib の Figure を OriginLab グラフに変換するシステム。Origin のインストール状況に応じてローカル実行とリモート実行を自動切替する。

**Tech stack:** Python 3.14 / pyenv + uv / ruff + mypy + pytest / FastAPI / SQLite

**Monorepo structure:**

```
matplotlib-to-originlab/
├── client/   matplotlib-to-originlab         ユーザー向けクライアント（全OS）
├── core/     matplotlib-to-originlab-core    ローカル実行エンジン（Windows + Origin）
├── remote/   matplotlib-to-originlab-remote  HTTP クライアント（サーバーモード用）
├── server/   matplotlib-to-originlab-server  Origin 実行ノード（FastAPI, Windows）
├── tests/    統合テスト
├── docs/     アーキテクチャ・仕様・ファイルマップ等
└── docs/dev-charter/  開発憲章（git subtree）
```

**Platform split:**
- Windows のみ: `core/`（originpro + win32com）、`server/`
- クロスプラットフォーム: `client/`、`remote/`

**Ruff スコープ:** `remote/` と `server/` のみ（`core/`・`client/` は除外）

---

## Applied Charter Principles

憲章参照: `docs/dev-charter/CHARTER_INDEX.md` でトピックを特定してから該当ファイルのみ読む

- **Conventional Commits**（feat/fix/docs/chore）でコミットする
- **変更範囲は必要最小限**（YAGNI）、3 回目の重複で初めて抽象化を検討
- **コメントは「なぜ」のみ**。コードから自明な処理には書かない
- **セキュリティ:** secrets はコードに書かず環境変数で管理。`.env` はコミット禁止
- **CI 必須:** security → lint → test → build の順。`build` job が全集約点
- **main への直接 push 禁止**。PR 経由でのみマージ
- **外部公開面は英語必須**（コミットメッセージ・PR・docstring・エラーメッセージ）

---

## Document Sync Rule

仕様・ルール・構成に変更が生じたとき、変更と同じ作業内で関連ドキュメントを更新する。
対象は docs/ 内のファイルに限らず、AI_CONTEXT.md・README.md 等のルートファイルも含む。

---

## Project-Specific Rules

### Origin Constraints (Critical)
- Origin は「単一計算ノード」: **並列処理禁止**、常に 1 ジョブのみ実行
- Origin アクセスは常に `threading.Lock()` 内で行う
- 各ジョブ間で必ず状態リセット（`doc -n;` で新規プロジェクト）

### Architecture
```
[User Code] → client → core（local）or remote（HTTP）
                              ↓
                        server（FastAPI）→ Job DB（SQLite）→ Worker → Origin
```

### API Specification (server)
- `POST /job` — ジョブ投入 → `{ "job_id": "uuid" }`
- `GET /job/{job_id}` — ステータス確認
- `GET /result/{job_id}` — 結果取得（.opju or .pptx）
- `POST /job/{job_id}/cancel` — キャンセル
- 認証: `Authorization: Bearer <token>`（環境変数 `MATPLOTLIB_TO_ORIGINLAB_TOKEN`）
- 通信: HTTPS（自己署名証明書）、研究室 LAN 内のみを前提

### Timeout
- `MAX_RUNTIME = 300` 秒。超過時は Origin 強制終了 → 再起動 → job → timeout

### figure_data Schema
```json
{
  "graphs": [{ "type": "line|scatter|bar", "x": [], "y": [], "title": "", ... }],
  "output_format": "opju | pptx",
  "pptx_layout": { "graphs_per_slide": 1 }
}
```

### Test Policy
- Linux CI: respx モック（Origin 不要）でリモート・サーバー HTTP 層をテスト
- Windows self-hosted: `test-origin` label 付き PR または main push 時のみ実行

---

## AI Tool Assignments

- **使用ツール**：Claude Code、GitHub Copilot、Gemini CLI
- **標準担当の正本**：[docs/dev-charter/AI_COLLABORATION_RULES.md](docs/dev-charter/AI_COLLABORATION_RULES.md) の「AI Tool Responsibilities」と「Rules for Multi-AI Usage」
- **プロジェクト固有の上書き**：Codex 未使用のため、Codex 担当のコードレビュー・バグ調査は Claude Code が兼務する

---

## Prohibited Actions

- secrets・認証情報のコードへのハードコード / コミット
- `.env` ファイルのコミット（`.env.example` はコミット可）
- ローカル絶対パスのソースコードへのハードコード
- Origin への並列アクセス
- `main` への直接 push
- AI との会話ログのコミット
- `docs/dev-charter/` 配下のファイルの直接編集（変更は dev-charter リポジトリ本体に Issue を立て `git subtree pull` で取り込む）
