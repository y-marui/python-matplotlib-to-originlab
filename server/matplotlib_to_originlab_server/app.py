"""FastAPI application for matplotlib-to-originlab-server.

Endpoints
---------
POST   /job                  Submit a job, returns job_id
GET    /job/{job_id}         Poll job status
GET    /result/{job_id}      Download the result file
POST   /job/{job_id}/cancel  Cancel a queued or running job
GET    /queue                Inspect the full job queue (ops use)
GET    /health               Liveness check
GET    /version              Package version info

Start the server
----------------
    python -m matplotlib_to_originlab_server
    matplotlib-to-originlab-server --host 0.0.0.0 --port 8719
"""

from __future__ import annotations

import ipaddress
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import FileResponse, JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError as exc:
    raise ImportError(
        "matplotlib-to-originlab-server requires fastapi and uvicorn. "
        "Install with: pip install 'matplotlib-to-originlab-server[server]'"
    ) from exc

from . import db, worker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JOBS_DIR: Path = worker.JOBS_DIR
BEARER_TOKEN: str | None = os.environ.get("MATPLOTLIB_TO_ORIGINLAB_TOKEN")

# Comma-separated list of allowed client IPs / CIDR networks.
# Example: "127.0.0.1,192.168.1.0/24"
# Leave unset (or empty) to allow all clients.
_raw_allow = os.environ.get("MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS", "").strip()
ALLOW_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
if _raw_allow:
    for _entry in _raw_allow.split(","):
        _entry = _entry.strip()
        if _entry:
            try:
                ALLOW_NETWORKS.append(ipaddress.ip_network(_entry, strict=False))
            except ValueError:
                # Try treating it as a bare host address
                ALLOW_NETWORKS.append(ipaddress.ip_network(_entry + "/32", strict=False))

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(title="matplotlib-to-originlab-server")


class _BearerTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[len("Bearer "):] != BEARER_TOKEN:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


class _IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Reject requests from IPs not in ALLOW_NETWORKS."""

    async def dispatch(self, request: Request, call_next):
        client_ip_str = request.client.host if request.client else ""
        try:
            client_addr = ipaddress.ip_address(client_ip_str)
        except ValueError:
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        if not any(client_addr in net for net in ALLOW_NETWORKS):
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        return await call_next(request)


if BEARER_TOKEN:
    app.add_middleware(_BearerTokenMiddleware)

if ALLOW_NETWORKS:
    app.add_middleware(_IPAllowlistMiddleware)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _on_startup():
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    db.init_db()
    db.recover_running_jobs()
    worker.start_worker()


@app.on_event("shutdown")
async def _on_shutdown():
    worker.stop_worker()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/job", status_code=201)
async def submit_job(request: Request):
    """Accept a figure_data payload and enqueue it."""
    body = await request.json()
    figure_data = body.get("figure_data")
    if not figure_data:
        raise HTTPException(status_code=422, detail="Missing 'figure_data' in request body")

    job_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    # Persist input to disk for reproducibility / debugging
    input_dir = JOBS_DIR / job_id / "input"
    input_dir.mkdir(parents=True)
    (input_dir / "figure_data.json").write_text(
        json.dumps(figure_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    db.create_job(job_id, json.dumps(figure_data), created_at)
    return {"job_id": job_id}


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Return current status of a job."""
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job["status"]}


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """Download the result file for a completed job."""
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "success":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not complete (current status: {job['status']!r})",
        )
    result_path = job.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="Result file not found on disk")
    return FileResponse(result_path)


@app.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a queued or running job."""
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job["status"]

    if status == "queued":
        db.update_job(job_id, status="cancelled")
        return {"job_id": job_id, "status": "cancelled"}

    if status == "running":
        # Mark cancelled first so the worker thread won't override it,
        # then kill Origin so the blocking COM call raises and the thread exits.
        db.update_job(
            job_id,
            status="cancelled",
            finished_at=datetime.now(timezone.utc).isoformat(),
            error="Cancelled by user",
        )
        worker.force_restart_origin()
        return {"job_id": job_id, "status": "cancelled"}

    raise HTTPException(
        status_code=409,
        detail=f"Cannot cancel a job with status {status!r}",
    )


@app.get("/queue")
async def get_queue():
    """Return all jobs ordered by creation time (newest first)."""
    return {"jobs": db.get_all_jobs()}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "auth": "bearer" if BEARER_TOKEN else "none",
        "ip_allowlist": bool(ALLOW_NETWORKS),
    }


@app.get("/version")
async def version():
    from matplotlib_to_originlab_server import __version__ as server_ver
    try:
        from matplotlib_to_originlab_core import __version__ as core_ver
    except Exception:
        core_ver = "unavailable"
    return {"server": server_ver, "core": core_ver}


# ---------------------------------------------------------------------------
# Entry point (used by __main__.py and the console script)
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError(
            "uvicorn is required to run the server. "
            "Install with: pip install 'matplotlib-to-originlab-server[server]'"
        ) from exc

    parser = argparse.ArgumentParser(
        prog="matplotlib-to-originlab-server",
        description="Origin execution node for matplotlib-to-originlab",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8719, help="Bind port (default: 8719)")
    parser.add_argument("--ssl-certfile", default=None, help="Path to SSL certificate file")
    parser.add_argument("--ssl-keyfile", default=None, help="Path to SSL private key file")
    parser.add_argument(
        "--allow-ips",
        default=None,
        help=(
            "Comma-separated list of allowed client IPs / CIDR networks "
            "(e.g. '127.0.0.1,192.168.1.0/24'). "
            "Overrides the MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS env var. "
            "Leave unset to allow all clients."
        ),
    )
    args = parser.parse_args()

    # CLI --allow-ips overrides the env var at startup
    if args.allow_ips is not None:
        os.environ["MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS"] = args.allow_ips

    uvicorn.run(
        "matplotlib_to_originlab_server.app:app",
        host=args.host,
        port=args.port,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
    )


if __name__ == "__main__":
    main()
