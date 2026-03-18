# Matplotlib to Originlab — Roadmap

This document tracks planned work across the monorepo.

---

## Package status

| Package                           | Status       | PyPI |
|-----------------------------------|--------------|------|
| matplotlib-to-originlab-core      | Functional   | No (local path only) |
| matplotlib-to-originlab           | Functional   | Planned |
| matplotlib-to-originlab-remote    | Stub         | Planned |
| matplotlib-to-originlab-server    | Stub         | Planned |

---

## Phase 1 — Package structure (current)

- [x] Move `py2origin` → `core/matplotlib_to_originlab_core`
- [x] Create `client/matplotlib_to_originlab` facade with `origin_available()` routing
- [x] Create stub `remote/matplotlib_to_originlab_remote`
- [x] Create stub `server/matplotlib_to_originlab_server`
- [x] Per-package `pyproject.toml` files
- [x] `ROADMAP.md` (this file)

---

## Phase 2 — Core improvements

These are known gaps in the existing `matplotlib-to-originlab-core` implementation:

- [ ] Font size of x / y axis labels (`layer.x.label.pt`, `xb.fsize`)
- [ ] Font size of legend
- [ ] Support `matplotlib.pyplot.errorbar` with `xerr` (currently only `yerr`)
- [ ] Fix `warningszw` typo → `warnings` (done in Phase 1)
- [ ] Support subplots / multiple layers
- [ ] Support double y-axis or double x-axis
- [ ] Astropy units: full round-trip (currently partial)
- [ ] Test suite beyond version check

---

## Phase 3 — Remote transport (`matplotlib-to-originlab-remote`)

Implement the HTTP client in `remote/matplotlib_to_originlab_remote/__init__.py`:

- [ ] Extract figure info from matplotlib Figure and serialise to `figure_data` JSON (see `AI_CONTEXT.md` §5 for schema)
- [ ] `POST /job` — submit job, receive `job_id`
- [ ] `GET /job/{job_id}` — poll for status (`queued | running | success | failed | timeout | cancelled`)
- [ ] `GET /result/{job_id}` — download .opju or .pptx result
- [ ] `POST /job/{job_id}/cancel` — cancel queued or running job
- [ ] Polling helper: 3s interval, 360s timeout (see `AI_CONTEXT.md` §7)
- [ ] HTTPS with self-signed cert (`verify=False` or cert path)
- [ ] Bearer token authentication via env var
- [ ] `configure()` picks up `MATPLOTLIB_TO_ORIGINLAB_SERVER_URL` env var (stub exists)
- [ ] Unit tests with `pytest-asyncio` + `respx` (mock server)

---

## Phase 4 — Server (`matplotlib-to-originlab-server`)

Implement the FastAPI server in `server/matplotlib_to_originlab_server/app.py`.
Full spec: see `AI_CONTEXT.md`.

- [ ] SQLite job DB (`jobs` table — see `AI_CONTEXT.md` §8)
- [ ] Job directory structure: `/jobs/{job_id}/input/`, `output/`, `log.txt`
- [ ] `POST /job` — accept `figure_data`, return `job_id`, enqueue
- [ ] `GET /job/{job_id}` — return job status
- [ ] `GET /result/{job_id}` — return .opju or .pptx as binary
- [ ] `POST /job/{job_id}/cancel` — cancel queued job or kill running Origin
- [ ] `GET /queue` — return current queue state (ops use)
- [ ] Single-threaded FIFO worker (see `AI_CONTEXT.md` §9)
- [ ] Origin control via win32com with `threading.Lock()` (see `AI_CONTEXT.md` §10–11)
- [ ] State reset: `doc -s;` between jobs; full restart on failure/timeout
- [ ] Startup recovery: `running → queued` on server restart
- [ ] Structured per-job logging to `log.txt` + DB summary
- [ ] `MAX_RUNTIME = 300` s timeout with watchdog
- [ ] Bearer token middleware (env var)
- [ ] HTTPS (self-signed cert) + optional IP allowlist
- [ ] `--host` / `--port` CLI arguments (via `argparse` or `typer`)
- [ ] Windows service / auto-start setup instructions
- [ ] Integration tests (client ↔ server in CI, Windows runner)

---

## Phase 5 — Distribution

- [ ] Publish `matplotlib-to-originlab` to PyPI
- [ ] Publish `matplotlib-to-originlab-remote` to PyPI (bundled with client)
- [ ] Publish `matplotlib-to-originlab-server` to PyPI
- [ ] `matplotlib-to-originlab-core` stays local (not on PyPI)
- [ ] GitHub Actions CI:
  - Lint / type check (all packages)
  - Tests on Linux (client + remote stubs)
  - Tests on Windows with OriginLab (core + server, self-hosted runner)
- [ ] Versioning strategy (single version across monorepo vs. independent)

---

## Architecture reference

```
[User Code]
    ↓
matplotlib-to-originlab  (client)
    ↓
┌────────────────────────────────────┐
│  origin_available() == True        │
│    → matplotlib-to-originlab-core  │
│                                    │
│  origin_available() == False       │
│    → matplotlib-to-originlab-remote│
└────────────────────────────────────┘
    ↓ (remote path, HTTPS + Bearer token)
matplotlib-to-originlab-server (FastAPI)
    ↓
Job DB (SQLite)  ←→  Job Queue
    ↓
Worker (Single Thread)
    ↓
Origin (COM / win32com)
    ↓
Result Storage (.opju / .pptx)
    ↓
client (polling GET /job/{id} → GET /result/{id})
```

See `AI_CONTEXT.md` for full technical specification.

### origin_available() logic

```python
@lru_cache(maxsize=1)
def origin_available() -> bool:
    try:
        import win32com.client
        win32com.client.Dispatch("Origin.Application")
        return True
    except Exception:
        return False
```

Result is cached for the process lifetime to avoid repeatedly launching Origin.

### mode parameter

| mode     | Behaviour                                                        |
|----------|------------------------------------------------------------------|
| "auto"   | `origin_available()` decides (default)                           |
| "local"  | Always use core (fails if Origin is not available)               |
| "remote" | Always use remote transport → server                             |

---

## Dependency graph

```
matplotlib-to-originlab (client)
├── matplotlib-to-originlab-core   [Windows only, path reference]
└── matplotlib-to-originlab-remote

matplotlib-to-originlab-remote
└── httpx

matplotlib-to-originlab-server
└── matplotlib-to-originlab-core   [Windows only, path reference]
   (+ fastapi, uvicorn — optional)
```
