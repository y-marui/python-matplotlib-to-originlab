# matplotlib-to-origin — Roadmap

This document tracks planned work across the monorepo.

---

## Package status

| Package                        | Status       | PyPI |
|--------------------------------|--------------|------|
| matplotlib-to-origin-core      | Functional   | No (local path only) |
| matplotlib-to-origin           | Functional   | Planned |
| matplotlib-to-origin-remote    | Stub         | Planned |
| matplotlib-to-origin-server    | Stub         | Planned |

---

## Phase 1 — Package structure (current)

- [x] Move `py2origin` → `core/matplotlib_to_origin_core`
- [x] Create `client/matplotlib_to_origin` facade with `origin_available()` routing
- [x] Create stub `remote/matplotlib_to_origin_remote`
- [x] Create stub `server/matplotlib_to_origin_server`
- [x] Per-package `pyproject.toml` files
- [x] `ROADMAP.md` (this file)

---

## Phase 2 — Core improvements

These are known gaps in the existing `matplotlib-to-origin-core` implementation:

- [ ] Font size of x / y axis labels (`layer.x.label.pt`, `xb.fsize`)
- [ ] Font size of legend
- [ ] Support `matplotlib.pyplot.errorbar` with `xerr` (currently only `yerr`)
- [ ] Fix `warningszw` typo → `warnings` (done in Phase 1)
- [ ] Support subplots / multiple layers
- [ ] Support double y-axis or double x-axis
- [ ] Astropy units: full round-trip (currently partial)
- [ ] Test suite beyond version check

---

## Phase 3 — Remote transport (`matplotlib-to-origin-remote`)

Implement the HTTP client in `remote/matplotlib_to_origin_remote/__init__.py`:

- [ ] Choose serialisation format for matplotlib Figure
  - Candidate: pickle + base64 (simple, lossy on cross-version transfers)
  - Candidate: JSON + array data (portable, requires custom encoder)
- [ ] Implement `run()` with `httpx` POST to `/run`
- [ ] Job polling or WebSocket for async results
- [ ] Authentication / API key support
- [ ] `configure()` picks up `MATPLOTLIB_TO_ORIGIN_SERVER_URL` env var (stub exists)
- [ ] Unit tests with `pytest-asyncio` + `respx` (mock server)

---

## Phase 4 — Server (`matplotlib-to-origin-server`)

Implement the FastAPI server in `server/matplotlib_to_origin_server/app.py`:

- [ ] `GET /health` — return Origin availability and server version
- [ ] `GET /version` — return package versions
- [ ] `POST /run` — accept serialised figure, execute via core, return result
- [ ] Job queue (background tasks) for concurrent requests
- [ ] `--host` / `--port` CLI arguments (via `argparse` or `typer`)
- [ ] Windows service / auto-start setup instructions
- [ ] Authentication / API key middleware
- [ ] Integration tests (client ↔ server in CI, Windows runner)

---

## Phase 5 — Distribution

- [ ] Publish `matplotlib-to-origin` to PyPI
- [ ] Publish `matplotlib-to-origin-remote` to PyPI (bundled with client)
- [ ] Publish `matplotlib-to-origin-server` to PyPI
- [ ] `matplotlib-to-origin-core` stays local (not on PyPI)
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
matplotlib-to-origin  (client)
    ↓
┌────────────────────────────────────┐
│  origin_available() == True        │
│    → matplotlib-to-origin-core     │
│                                    │
│  origin_available() == False       │
│    → matplotlib-to-origin-remote   │
└────────────────────────────────────┘
    ↓ (remote path)
matplotlib-to-origin-server
    ↓
OriginLab
```

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
matplotlib-to-origin (client)
├── matplotlib-to-origin-core   [Windows only, path reference]
└── matplotlib-to-origin-remote

matplotlib-to-origin-remote
└── httpx

matplotlib-to-origin-server
└── matplotlib-to-origin-core   [Windows only, path reference]
   (+ fastapi, uvicorn — optional)
```
