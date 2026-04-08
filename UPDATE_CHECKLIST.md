# dev-charter Update Checklist

After running `git subtree pull` to update dev-charter in your project, paste the following prompts into your AI tool in order.

## Step 1 — Bulk update

```
Read all files in docs/dev-charter/ and update the project to reflect charter changes:

1. Update AI context files following the spec in docs/dev-charter/AI_TOOL_SETUP.md
2. Review the impact of charter changes on the entire project (CI, security, docs, license, etc.) and fix as needed
3. Read docs/dev-charter/topics/PROJECT_README_GUIDELINES.md and update the project README to reflect any changes
4. Read docs/dev-charter/topics/GITHUB_SETTINGS.md and apply any setting changes that can be configured via gh commands

- If AI_CONTEXT.md does not exist, use the install prompt instead
- If a charter change conflicts with a project-specific rule, list the conflicts and confirm priority with the user
- Do not commit after completing (let the user review first)
```

## Step 2 — File-by-file review

```
Re-read each file in docs/dev-charter/ one at a time and verify that the project fully reflects it.

For each file in order:
1. Read the file
2. Check the corresponding project files and settings
3. Fix anything that is missing or incomplete

- Re-check items already addressed in Step 1
- Do not commit after completing (let the user review first)
```

---

*この文書には日本語版があります。編集時は同一コミットで更新してください。*

# dev-charter 更新チェックリスト

`git subtree pull` で dev-charter を更新した後、以下のプロンプトを順に AI に貼り付けて実行してください。

## Step 1 — 一括更新

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

## Step 2 — ファイル単位の精査

```
docs/dev-charter/ 内の各ファイルを1つずつ読み直し、プロジェクトへの反映を確認・補完してください。

各ファイルについて順に:
1. ファイルを読む
2. 対応するプロジェクトファイル・設定を確認する
3. 未反映・不十分な箇所があれば修正する

- Step 1 で対応済みの箇所も再確認する
- 完了後はコミットしない（ユーザーが確認してから行う）
```

---

*This document has a Japanese version above. Update both in the same commit when editing.*
