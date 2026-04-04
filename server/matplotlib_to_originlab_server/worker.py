"""Background worker — single-threaded FIFO executor for Origin jobs."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import db

logger = logging.getLogger(__name__)

MAX_RUNTIME: int = int(os.environ.get("MTO_MAX_RUNTIME", "300"))
JOBS_DIR: Path = Path(os.environ.get("MTO_JOBS_DIR", "jobs"))

# Protects all Origin COM access.  Single-threaded by design, but the lock
# also guards against accidental re-entry from cancel calls.
_origin_lock = threading.Lock()

_stop_event = threading.Event()
_worker_thread: threading.Thread | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def _log(job_id: str, message: str) -> None:
    log_path = _job_dir(job_id) / "log.txt"
    ts = _now()
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except OSError:
        logger.warning("Could not write to log for job %s", job_id)


# ---------------------------------------------------------------------------
# Origin process management
# ---------------------------------------------------------------------------


def force_restart_origin() -> None:
    """Kill all running Origin processes.  The next job will re-attach."""
    logger.warning("Forcing Origin restart")
    for exe in ("Origin.exe", "Origin64.exe"):
        subprocess.run(
            ["taskkill", "/F", "/IM", exe],
            capture_output=True,
        )
    time.sleep(5)  # allow OS to clean up handles


# ---------------------------------------------------------------------------
# Figure reconstruction + core execution
# ---------------------------------------------------------------------------


def _reconstruct_and_run(figure_data: dict, output_dir: Path) -> Path:
    """Rebuild a matplotlib figure from *figure_data* and run the core.

    Returns the path to the saved result file.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import originpro as op
    from matplotlib_to_originlab_core import matplotlib_to_origin

    fig, ax = plt.subplots()

    # --- reconstruct plots ---
    for plot in figure_data.get("plots", []):
        x = np.array(plot["x"])
        y = np.array(plot["y"])
        label = plot.get("label", "")
        color = plot.get("color")
        linestyle = plot.get("linestyle") or "-"
        marker = plot.get("marker", "None")
        if marker == "None":
            marker = None
        markersize = plot.get("markersize", 6)
        mec = plot.get("mec", color)
        mfc = plot.get("mfc", color)
        mew = plot.get("mew", 1.5)
        linewidth = plot.get("linewidth", 1.5)
        yerr = plot.get("yerr")

        if plot["type"] == "errorbar":
            xerr = plot.get("xerr")
            ax.errorbar(
                x,
                y,
                yerr=np.array(yerr) if yerr is not None else None,
                xerr=np.array(xerr) if xerr is not None else None,
                fmt="o" if marker else "-",
                label=label,
                color=color,
                mec=mec,
                mfc=mfc,
                linewidth=linewidth,
            )
        elif plot["type"] == "scatter":
            ax.plot(
                x,
                y,
                linestyle="None",
                marker=marker or "o",
                markersize=markersize,
                label=label,
                color=color,
                mec=mec,
                mfc=mfc,
                mew=mew,
            )
        else:  # "line" or "line+scatter"
            ax.plot(
                x,
                y,
                linestyle=linestyle,
                marker=marker,
                markersize=markersize,
                label=label,
                color=color,
                mec=mec,
                mfc=mfc,
                mew=mew,
                linewidth=linewidth,
            )

    # --- reconstruct bar groups ---
    for bar_group in figure_data.get("bars", []):
        x_cats = bar_group["x_categories"]
        x_pos = np.arange(len(x_cats))
        groups = bar_group["groups"]
        n = len(groups)
        width = 0.8 / n
        for i, group in enumerate(groups):
            ax.bar(
                x_pos + i * width - 0.4 + width / 2,
                group["y"],
                width=width,
                label=group["label"],
                color=group["color"],
            )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_cats)

    # --- axis metadata ---
    ax.set_xlabel(figure_data.get("xlabel", ""))
    ax.set_ylabel(figure_data.get("ylabel", ""))
    ax.set_xscale(figure_data.get("xscale", "linear"))
    ax.set_yscale(figure_data.get("yscale", "linear"))
    xlim = figure_data.get("xlim")
    ylim = figure_data.get("ylim")
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    figsize = figure_data.get("figsize")
    if figsize:
        fig.set_size_inches(figsize)
    legend_title = figure_data.get("legend_title", "")
    if any(p.get("label") for p in figure_data.get("plots", [])):
        ax.legend(title=legend_title or None)

    output_format = figure_data.get("output_format", "opju")
    result_stem = str(output_dir / "result")

    with _origin_lock:
        # Reset Origin state between jobs so leftover workbooks / graphs from
        # the previous job do not pollute this one.  asksave=False suppresses
        # any save dialog (safe because each job saves explicitly beforehand).
        op.new(asksave=False)
        matplotlib_to_origin(
            fig,
            ax,
            folder_name=figure_data.get("folder_name"),
            workbook_name=figure_data.get("workbook_name", "Book"),
            worksheet_name=figure_data.get("worksheet_name", "Sheet"),
            graph_name=figure_data.get("graph_name", "Graph"),
        )
        # Save the Origin project to the output directory.
        # LabTalk `save` appends .opju automatically.
        op.lt_exec(f"save {result_stem};")

    plt.close(fig)

    result_path = output_dir / f"result.{output_format}"
    if not result_path.exists():
        # Fall back to .opju if pptx was requested but not yet supported
        opju_path = output_dir / "result.opju"
        if opju_path.exists():
            result_path = opju_path
    return result_path


# ---------------------------------------------------------------------------
# Job execution
# ---------------------------------------------------------------------------


def _run_job(job: dict) -> None:
    """Execute a single job.  Updates the DB with the outcome."""
    job_id: str = job["id"]
    job_dir = _job_dir(job_id)
    output_dir = job_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    started_at = _now()
    db.update_job(job_id, status="running", started_at=started_at)
    _log(job_id, "Job started")

    figure_data: dict = json.loads(job["figure_data"])

    exc_holder: list[Exception] = []
    path_holder: list[Path] = []

    # Origin COM objects have STA thread affinity — all Origin calls must run
    # in the same thread that first imported originpro.  We therefore run
    # _reconstruct_and_run directly in the worker thread and use a lightweight
    # watchdog thread only to kill Origin if the job exceeds MAX_RUNTIME.
    _job_done = threading.Event()
    _killed_by_watchdog = threading.Event()

    def _watchdog() -> None:
        if _job_done.wait(timeout=MAX_RUNTIME):
            return  # job finished before timeout
        _killed_by_watchdog.set()
        force_restart_origin()

    watchdog = threading.Thread(target=_watchdog, daemon=True)
    watchdog.start()

    try:
        path = _reconstruct_and_run(figure_data, output_dir)
        path_holder.append(path)
    except Exception as exc:
        exc_holder.append(exc)
    finally:
        _job_done.set()  # signal watchdog that work is done

    finished_at = _now()

    # Don't override a status that was set externally (e.g. cancel).
    current = db.get_job(job_id)
    if current and current["status"] == "cancelled":
        _log(job_id, "Job was cancelled externally")
        return

    if _killed_by_watchdog.is_set():
        _log(job_id, f"Timeout after {MAX_RUNTIME}s — restarting Origin")
        force_restart_origin()
        db.update_job(
            job_id,
            status="timeout",
            finished_at=finished_at,
            error=f"Execution timed out after {MAX_RUNTIME}s",
        )
        _log(
            job_id,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "timeout",
                    "execution_time": MAX_RUNTIME,
                    "error": "timeout",
                }
            ),
        )
    elif exc_holder:
        err = str(exc_holder[0])
        _log(job_id, f"Job failed: {err}")
        db.update_job(job_id, status="failed", finished_at=finished_at, error=err)
        _log(
            job_id,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "failed",
                    "execution_time": None,
                    "error": err,
                }
            ),
        )
    else:
        result_path = path_holder[0] if path_holder else None
        result_path_str = str(result_path) if result_path else None

        started_dt = datetime.fromisoformat(started_at)
        finished_dt = datetime.fromisoformat(finished_at)
        exec_time = (finished_dt - started_dt).total_seconds()

        db.update_job(
            job_id,
            status="success",
            finished_at=finished_at,
            result_path=result_path_str,
        )
        _log(
            job_id,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "success",
                    "execution_time": exec_time,
                    "error": None,
                }
            ),
        )


# ---------------------------------------------------------------------------
# Worker loop
# ---------------------------------------------------------------------------


def _worker_loop() -> None:
    while not _stop_event.is_set():
        job = db.get_next_queued_job()
        if job is None:
            time.sleep(1)
            continue
        try:
            _run_job(job)
        except Exception:
            logger.exception("Unexpected error in worker for job %s", job["id"])


def start_worker() -> threading.Thread:
    global _worker_thread
    _stop_event.clear()
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="origin-worker")
    _worker_thread.start()
    return _worker_thread


def stop_worker() -> None:
    _stop_event.set()
