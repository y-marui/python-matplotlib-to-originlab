# Dev Charter (開発憲章)

> **このファイルは正本（日本語版）です。**
> 英語版（参照）は [README.md](README.md) を参照してください。

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)
[![check-charter CI](https://github.com/y-marui/dev-charter/actions/workflows/check-charter.yml/badge.svg)](https://github.com/y-marui/dev-charter/actions/workflows/check-charter.yml)

AI支援ソフトウェアプロジェクトのための共有開発憲章。

このリポジトリは、プロジェクト横断的に使用される共通の哲学、アーキテクチャ原則、
および開発ルールを定義します。

## Documents

| ファイル | 内容 |
|---|---|
| [PRINCIPLES.md](PRINCIPLES.md) | 開発哲学・デザイン・アーキテクチャ原則 |
| [CODE_STYLE.md](CODE_STYLE.md) | コードスタイル |
| [AI_COLLABORATION_RULES.md](AI_COLLABORATION_RULES.md) | AI 協働ルールと役割分担 |
| [AI_CONTEXT_HIERARCHY.md](AI_CONTEXT_HIERARCHY.md) | AI コンテキスト優先階層 |
| [AI_TOOL_SETUP.md](AI_TOOL_SETUP.md) | AI コンテキストファイルの構成仕様（AI_CONTEXT.md・各ツール設定ファイル） |
| [LANGUAGE_POLICY.md](LANGUAGE_POLICY.md) | 言語ポリシー（正本＝日本語） |
| [LOCALIZATION_POLICY.md](LOCALIZATION_POLICY.md) | ローカライゼーションポリシー |
| [PROJECT_LIFECYCLE.md](PROJECT_LIFECYCLE.md) | プロジェクトライフサイクルと体制 |
| [UI_GUIDELINES.md](UI_GUIDELINES.md) | UI ガイドライン・カラー・アイコン |
| [MONETIZATION_POLICY.md](MONETIZATION_POLICY.md) | マネタイズポリシーとプラットフォーム別方針 |
| [SECURITY_POLICY.md](SECURITY_POLICY.md) | セキュリティポリシーとフック設定リファレンス |
| [LEGAL_POLICY.md](LEGAL_POLICY.md) | ライセンス選択基準・テンプレート（Closed / MIT / AGPL・GPL・LGPL） |
| [topics/CI_POLICY.md](topics/CI_POLICY.md) | CI job設計方針・Branch Protection Ruleset |
| [topics/GITHUB_SETTINGS.md](topics/GITHUB_SETTINGS.md) | GitHub リポジトリ設定確認（Ruleset・Sponsors） |
| [topics/GITHUB_CONTRIBUTING.md](topics/GITHUB_CONTRIBUTING.md) | Issue・PR・CONTRIBUTING.md・PRテンプレート・準CLA（OSS向け） |
| [topics/TEMPLATE_README_GUIDELINES.md](topics/TEMPLATE_README_GUIDELINES.md) | GitHub テンプレートリポジトリの README 設計規約（開発環境・言語・LICENSE・必須セクション） |
| [topics/PROJECT_README_GUIDELINES.md](topics/PROJECT_README_GUIDELINES.md) | テンプレートから作成したプロジェクトの README 整備手順 |

## How to Use

1. `git subtree` で `docs/dev-charter/` に取り込む
2. AI に dev-charter を読ませ、プロジェクトルートに `AI_CONTEXT.md` と AI ツール設定ファイルを生成させる
3. 憲章が更新されたら `git subtree pull` 後、AI にコンテキストファイルを追従させる

構成仕様は [AI_TOOL_SETUP.md](AI_TOOL_SETUP.md) を参照。

## Install (git subtree)

```
git remote add dev-charter https://github.com/y-marui/dev-charter
git fetch dev-charter
git subtree add --prefix=docs/dev-charter dev-charter main --squash
```

インストール後、以下のプロンプトを順に AI に貼り付けて実行する：

**Step 1 — 一括セットアップ**

```
docs/dev-charter/ 内の全ファイルを読み、このプロジェクトを調査した上で、以下を実施してください。

1. docs/dev-charter/AI_TOOL_SETUP.md の仕様に従い AI コンテキストファイルをセットアップする
2. 憲章の要件とプロジェクトの現状を照合し、未対応箇所をすべて特定・修正する
   （ファイル構成・CI・セキュリティ・ドキュメント・ライセンス・コーディング規約など、プロジェクト全体を対象とする）
3. docs/dev-charter/topics/PROJECT_README_GUIDELINES.md を読み、プロジェクトの README を検証・更新する
   （テンプレート形式の README はプロジェクト形式に再フォーマットし、存在しない場合は新規作成する）
4. docs/dev-charter/topics/GITHUB_SETTINGS.md を読み、gh コマンドで適用できるリポジトリ設定を実行する

- 不明点・確認事項は作業前に 1 回まとめて質問する
- 憲章と既存規約が矛盾する場合は矛盾点を列挙し、優先順位をユーザーに確認してから進める
- 大きなスコープになる場合は修正前にユーザーに確認する
- 完了後はコミットしない（ユーザーが確認してから行う）
```

**Step 2 — ファイル単位の精査**

```
docs/dev-charter/ 内の各ファイルを1つずつ読み直し、プロジェクトへの反映を確認・補完してください。

各ファイルについて順に:
1. ファイルを読む
2. 対応するプロジェクトファイル・設定を確認する
3. 未反映・不十分な箇所があれば修正する

- Step 1 で対応済みの箇所も再確認する
- 完了後はコミットしない（ユーザーが確認してから行う）
```

## Update

`dev-charter` リモートが未設定の場合（プロジェクトを clone した直後など）は先に追加する：

```
git remote add dev-charter https://github.com/y-marui/dev-charter
```

```
git subtree pull --prefix=docs/dev-charter dev-charter main --squash
```

更新後、以下のプロンプトを順に AI に貼り付けて実行する：

**Step 1 — 一括更新**

```
docs/dev-charter/ 内の全ファイルを読み、憲章の変更が影響する箇所を更新してください。

1. docs/dev-charter/AI_TOOL_SETUP.md の仕様に従い AI コンテキストファイルを更新する
2. 憲章の変更がプロジェクト全体（CI・セキュリティ・ドキュメント・ライセンス等）に与える影響を確認し修正する
3. docs/dev-charter/topics/PROJECT_README_GUIDELINES.md を読み、プロジェクトの README を変更内容に合わせて更新する
4. docs/dev-charter/topics/GITHUB_SETTINGS.md を読み、gh コマンドで適用できる設定変更を実行する

- AI_CONTEXT.md が存在しない場合はインストール用プロンプトを使うこと
- 憲章の変更がプロジェクト固有ルールと矛盾する場合は矛盾点を列挙してユーザーに確認する
- 完了後はコミットしない（ユーザーが確認してから行う）
```

**Step 2 — ファイル単位の精査**

```
docs/dev-charter/ 内の各ファイルを1つずつ読み直し、プロジェクトへの反映を確認・補完してください。

各ファイルについて順に:
1. ファイルを読む
2. 対応するプロジェクトファイル・設定を確認する
3. 未反映・不十分な箇所があれば修正する

- Step 1 で対応済みの箇所も再確認する
- 完了後はコミットしない（ユーザーが確認してから行う）
```

## Makefile Helper

```
update-charter:
	git remote | grep -q '^dev-charter$$' || \
	  git remote add dev-charter https://github.com/y-marui/dev-charter
	git fetch dev-charter
	git subtree pull --prefix=docs/dev-charter dev-charter main --squash
```

## Version Check (CI)

`.github/workflows/dev-charter-check.yml` をプロジェクトに追加すると、
毎週自動で最新バージョンを確認し、古い場合は update PR を作成します。

```yaml
name: Dev Charter
on:
  schedule:
    - cron: "23 3 * * 1"  # 毎週月曜 3:23 UTC
  workflow_dispatch:

jobs:
  check:
    name: Check
    uses: y-marui/dev-charter/.github/workflows/check-charter.yml@main
    with:
      fail_if_outdated: true
    permissions:
      contents: write
      pull-requests: write
```

> **Note:** Branch Protection で direct push が禁止されている場合は、
> GitHub Actions bot の bypass rule を追加してください
> （Settings > Rules > Rulesets > Bypass list > GitHub Actions）。

## Badge for Adopting Projects

プロジェクトの README にこのバッジを追加すると、dev-charter の更新状態を可視化できます。

### Workflow Status Badge

dev-charter が最新かどうかを表示します。バッジが機能するには上記ワークフローに `fail_if_outdated: true` が必要です。

```markdown
[![Charter Check](https://github.com/{owner}/{repo}/actions/workflows/dev-charter-check.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/dev-charter-check.yml)
```

`{owner}` と `{repo}` を自分のリポジトリのオーナー名・リポジトリ名に置き換えてください。

| 状態 | Status Badge |
|---|---|
| 未導入 / CI 未設定 | 赤（VERSION not found） |
| 導入済み・最新 | 緑 |
| 導入済み・更新必要 | 赤 |

---

*この文書には英語版 [README.md](README.md) があります。編集時は同一コミットで更新してください。*
