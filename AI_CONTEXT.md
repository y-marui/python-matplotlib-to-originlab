# AI_CONTEXT — matplotlib-to-originlab Remote Execution System

このファイルはAIアシスタントがこのプロジェクトに作業する際に参照する技術仕様書です。

---

## 1. 目的

異なるOS（Mac / Windows）から、matplotlib-to-originlab-serverを安全かつ再現性高く利用するためのリモート実行基盤を構築する。

---

## 2. アーキテクチャ

```
[User Code]
    ↓
matplotlib-to-originlab (client)
    ↓ Figure情報を抽出・JSON化
matplotlib-to-originlab-remote
    ↓ HTTPS
matplotlib-to-originlab-server (FastAPI)
    ↓
Job DB (SQLite)
    ↓
Job Queue
    ↓
Worker (Single Thread)
    ↓
Origin (COM制御)
    ↓
Result Storage (.opju / .pptx)
    ↓
clientへ返却
```

---

## 3. 設計方針

- **Originは「単一計算ノード」**: 並列処理禁止、常に1ジョブのみ実行
- **非同期ジョブ処理**: APIは即時レスポンス、実処理はバックグラウンド
- **完全なジョブ分離**: 各ジョブは独立ディレクトリ、ファイル共有禁止
- **再現性保証**: Origin状態のリセット必須、入力・出力・ログを保存

---

## 4. 通信仕様

- プロトコル: HTTPS（自己署名証明書）
- client側: `httpx.post(url, verify=False)` または証明書パスを指定
- 認証: `Authorization: Bearer <token>`（トークンは環境変数で管理）

---

## 5. figure_data スキーマ

```json
{
  "graphs": [
    {
      "type": "line | scatter | bar",
      "x": [],
      "y": [],
      "title": "",
      "xlabel": "",
      "ylabel": "",
      "xscale": "linear | log",
      "yscale": "linear | log",
      "legend": "",
      "color": "",
      "linestyle": "solid | dashed | dotted"
    }
  ],
  "output_format": "opju | pptx",
  "pptx_layout": {
    "graphs_per_slide": 1
  }
}
```

- `pptx_layout` は `output_format: "pptx"` のときのみ有効
- `graphs_per_slide` のデフォルトは1
- 1ジョブ = 複数グラフ = 1.opju（`graphs` 配列で表現）

---

## 6. API仕様

### POST /job — ジョブ投入

Request:
```json
{ "figure_data": { ... } }
```
Response:
```json
{ "job_id": "uuid" }
```

### GET /job/{job_id} — ステータス取得

Response:
```json
{
  "job_id": "uuid",
  "status": "queued | running | success | failed | timeout | cancelled"
}
```

### GET /result/{job_id} — 結果取得

- `output_format: "opju"` → .opjuファイル（バイナリ）
- `output_format: "pptx"` → .pptxファイル（バイナリ）

### POST /job/{job_id}/cancel — キャンセル

- `queued` → 即キャンセル
- `running` → Origin強制終了 → 再起動 → cancelled

### GET /queue — キュー確認（運用用）

---

## 7. 完了検知（ポーリング）

```python
def wait_for_result(job_id, interval=3, timeout=360):
    elapsed = 0
    while elapsed < timeout:
        status = get_job_status(job_id)
        if status in ("success", "failed", "timeout", "cancelled"):
            return status
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError("polling timeout")
```

- デフォルト間隔: 3秒
- ポーリングタイムアウト: 360秒（MAX_RUNTIME + バッファ）

---

## 8. データ設計

### Jobテーブル（SQLite）

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    status TEXT,
    created_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    figure_data TEXT,
    result_path TEXT,
    error TEXT
);
```

### ジョブディレクトリ構造

```
/jobs/
  └── {job_id}/
        ├── input/
        │     └── figure_data.json
        ├── output/
        │     └── result.opju or result.pptx
        └── log.txt
```

---

## 9. ワーカー仕様

- シングルスレッド、FIFO

```python
while True:
    job = fetch_next_job()
    mark_running(job)
    try:
        run_origin(job)
        mark_success(job)
    except Timeout:
        restart_origin()
        mark_timeout(job)
    except Exception as e:
        mark_failed(job, str(e))
```

---

## 10. Origin制御仕様

- 操作方法: COM経由（win32com）
- 状態リセット（標準）: `doc -s;`（LabTalk）
- 状態リセット（障害時）: Origin再起動

| 方法 | 安定性 | 速度 | 使用タイミング |
|------|--------|------|----------------|
| 毎回再起動 | ◎ | × | 障害時のみ |
| 新規プロジェクト | ○ | ◎ | 標準 |

---

## 11. タイムアウト・排他制御

```python
MAX_RUNTIME = 300  # 秒
lock = threading.Lock()
```

- タイムアウト超過時: Origin強制終了 → 再起動 → job → timeout
- Originアクセスは常にロック内

---

## 12. サーバー起動時の復元

```python
@app.on_event("startup")
async def recover_jobs():
    db.execute("UPDATE jobs SET status='queued' WHERE status='running'")
```

---

## 13. ログ設計

```json
{
  "job_id": "...",
  "status": "success",
  "execution_time": 12.3,
  "error": null
}
```

- 保存先: 各ジョブディレクトリ（log.txt）+ DBに概要保存

---

## 14. 障害対策

| 障害 | 対策 |
|------|------|
| Originフリーズ | watchdogで検知 → 強制kill → 再起動 |
| サーバー再起動 | 起動時に `running → queued` へ復元 |
| ディスク肥大化 | 定期削除（7日）— トリガーは後回し |

---

## 15. セキュリティ

- 前提: 研究室LAN内のみ利用
- HTTPS（自己署名証明書）
- APIキー認証（環境変数で管理）
- IP制限（推奨）

---

## 16. 運用ルール

- 最大実行時間: 300秒
- 定期再起動（1日1回推奨）

---

## 17. リスク評価

| リスク | 対策 |
|--------|------|
| Origin不安定 | 再起動 |
| ジョブ詰まり | タイムアウト |
| 再現性崩壊 | 状態リセット |
| データ競合 | ディレクトリ分離 |
| 通信傍受 | HTTPS |

---

## 18. 将来拡張（後回し）

- RedisによるQueue強化
- Web UI
- ジョブ優先度制御
- 分散Origin（複数Windows）
- 入力サイズ制限
