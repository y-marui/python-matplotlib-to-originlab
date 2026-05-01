# Specification

## Overview

matplotlib の Figure を OriginLab グラフに変換する。
Origin のインストール状況に応じてローカル実行（core）またはリモート実行（remote → server）を自動選択する。

---

## figure_data スキーマ

remote と server 間、および core との共通データフォーマット。

```json
{
  "plots": [
    {
      "type": "line | scatter | line+scatter | errorbar",
      "x": [1.0, 2.0, ...],
      "y": [4.0, 5.0, ...],
      "yerr": null,
      "xerr": null,
      "label": "Model1",
      "color": "#1f77b4",
      "linestyle": "-",
      "marker": "None",
      "markersize": 6.0,
      "mec": "#1f77b4",
      "mfc": "#1f77b4",
      "mew": 1.0,
      "linewidth": 1.5
    }
  ],
  "bars": [
    {
      "x_categories": ["A", "B", "C"],
      "groups": [
        { "label": "G1", "y": [1.0, 2.0, 3.0], "color": "#1f77b4" }
      ]
    }
  ],
  "xlabel": "X axis",
  "ylabel": "Y axis",
  "xscale": "linear | log",
  "yscale": "linear | log",
  "xlim": [0.0, 10.0],
  "ylim": [0.0, 100.0],
  "figsize": [6.4, 4.8],
  "legend_title": "",
  "output_format": "opju | pptx",
  "pptx_layout": { "graphs_per_slide": 1 },
  "folder_name": null,
  "workbook_name": "Book",
  "worksheet_name": "Sheet",
  "graph_name": "Graph"
}
```

---

## Server API エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| `POST` | `/job` | ジョブ投入。`figure_data` を JSON で送信 → `{ "job_id": "uuid" }` |
| `GET` | `/job/{job_id}` | ジョブステータス確認 → `{ "status": "queued|running|success|failed|timeout|cancelled" }` |
| `GET` | `/result/{job_id}` | 結果ファイル取得（`.opju` または `.pptx`） |
| `POST` | `/job/{job_id}/cancel` | ジョブキャンセル |
| `GET` | `/queue` | キュー全体を確認（運用用） |
| `GET` | `/health` | 生存確認 |
| `GET` | `/version` | パッケージバージョン情報 |

### 認証

`Authorization: Bearer <MATPLOTLIB_TO_ORIGINLAB_TOKEN>` ヘッダー必須。

### IP 制限

`MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS` 環境変数（カンマ区切り IP / CIDR）で接続元を制限できる。未設定時は全許可。

---

## Origin 制約

- Origin は「単一計算ノード」: **並列処理禁止**、常に 1 ジョブのみ実行
- Origin アクセスは常に `threading.Lock()` 内で行う
- 各ジョブ間で必ず状態リセット（`doc -n;` で新規プロジェクト）
- `MAX_RUNTIME = 300` 秒。超過時は Origin 強制終了 → 再起動 → job → timeout

---

## 環境変数

| 変数名 | デフォルト | 説明 |
|---|---|---|
| `MATPLOTLIB_TO_ORIGINLAB_SERVER_URL` | `http://localhost:8719` | リモートモード時のサーバー URL |
| `MATPLOTLIB_TO_ORIGINLAB_TOKEN` | なし | Bearer 認証トークン |
| `MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS` | なし（全許可） | 接続元 IP 制限 |

---

## 通信プロトコル

- HTTPS（自己署名証明書）、研究室 LAN 内のみを前提
- `verify=False`（デフォルト）で自己署名証明書を許容
