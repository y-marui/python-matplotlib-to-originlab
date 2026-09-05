"""matplotlib-to-originlab-remote — HTTP client for matplotlib-to-originlab-server.

This package is used automatically by matplotlib-to-originlab when
origin_available() returns False.  It serialises the matplotlib figure and
sends it to a running matplotlib-to-originlab-server instance.
"""

from __future__ import annotations

import os
import re
import time
import warnings
from pathlib import Path

import httpx
import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.container import BarContainer, ErrorbarContainer

__version__ = "0.1.0"
__all__ = ["run", "configure", "cancel"]

# Default server endpoint — override with configure() or env var.
_SERVER_URL: str = os.environ.get(
    "MATPLOTLIB_TO_ORIGINLAB_SERVER_URL", "http://localhost:8719"
).rstrip("/")
_BEARER_TOKEN: str | None = os.environ.get("MATPLOTLIB_TO_ORIGINLAB_TOKEN")


def configure(
    server_url: str | None = None,
    token: str | None = None,
) -> None:
    """Set the server URL and/or Bearer token.

    Parameters
    ----------
    server_url:
        Base URL of the server, e.g. ``"https://192.168.1.10:8719"``.
        Falls back to the ``MATPLOTLIB_TO_ORIGINLAB_SERVER_URL`` env var.
    token:
        Bearer token for authentication.
        Falls back to the ``MATPLOTLIB_TO_ORIGINLAB_TOKEN`` env var.
    """
    global _SERVER_URL, _BEARER_TOKEN
    if server_url is not None:
        _SERVER_URL = server_url.rstrip("/")
    if token is not None:
        _BEARER_TOKEN = token


# ---------------------------------------------------------------------------
# Figure serialisation
# ---------------------------------------------------------------------------


def _extract_figure_data(fig, ax, **kwargs) -> dict:
    """Extract matplotlib figure/axes state into a JSON-serialisable dict."""

    errorbar_containers = [c for c in ax.containers if isinstance(c, ErrorbarContainer)]
    container_children = {
        child for c in errorbar_containers for child in c.get_children()
    }

    plots: list[dict] = []

    # --- lines and errorbars ---
    line_entries = [
        (line, None) for line in ax.lines if line not in container_children
    ] + [(c.lines[0], c) for c in errorbar_containers]

    for line, container in line_entries:
        xdata = line.get_xdata()
        if hasattr(xdata, "value"):
            xdata = xdata.to(ax.xaxis.get_units()).value
        ydata = line.get_ydata()
        if hasattr(ydata, "value"):
            ydata = ydata.to(ax.yaxis.get_units()).value

        yerr = None
        xerr = None
        if container is None:
            raw_label = line.get_label()
            label = raw_label if not raw_label.startswith("_") else ""
            marker = plt.getp(line, "marker")
            linestyle = plt.getp(line, "linestyle")
            if marker == "None" and linestyle != "None":
                plot_type = "line"
            elif marker != "None" and linestyle == "None":
                plot_type = "scatter"
            else:
                plot_type = "line+scatter"
        elif isinstance(container, matplotlib.container.ErrorbarContainer):
            label = container.get_label() or ""
            plot_type = "errorbar"
            # Extract via barlinecols (robust for any capsize).
            # matplotlib stores barcols in order: xerr first, then yerr.
            _barcol_idx = 0
            if container.has_xerr:
                segs = container.lines[2][_barcol_idx].get_segments()
                xerr_arr = np.array([(s[1][0] - s[0][0]) / 2 for s in segs])
                if hasattr(xerr_arr, "value"):
                    xerr_arr = xerr_arr.to(ax.xaxis.get_units()).value
                xerr = np.float64(xerr_arr).tolist()
                _barcol_idx += 1
            if container.has_yerr:
                segs = container.lines[2][_barcol_idx].get_segments()
                yerr_arr = np.array([(s[1][1] - s[0][1]) / 2 for s in segs])
                if hasattr(yerr_arr, "value"):
                    yerr_arr = yerr_arr.to(ax.yaxis.get_units()).value
                yerr = np.float64(yerr_arr).tolist()
        else:
            warnings.warn(f"unknown container type {type(container)}, skipping")
            continue

        label = re.sub(r"\$(.+?)\$", r"\\q(\1)", label)

        plots.append(
            {
                "type": plot_type,
                "x": np.float64(xdata).tolist(),
                "y": np.float64(ydata).tolist(),
                "yerr": yerr,
                "xerr": xerr,
                "label": label,
                "color": mcolors.to_hex(plt.getp(line, "color")),
                "linestyle": plt.getp(line, "linestyle"),
                "marker": str(plt.getp(line, "marker")),
                "markersize": float(plt.getp(line, "ms")),
                "mec": mcolors.to_hex(plt.getp(line, "mec")),
                "mfc": mcolors.to_hex(plt.getp(line, "mfc")),
                "mew": float(plt.getp(line, "mew")),
                "linewidth": float(plt.getp(line, "linewidth")),
            }
        )

    # --- bar containers ---
    bar_containers = [c for c in ax.containers if isinstance(c, BarContainer)]
    bars: list[dict] = []
    if len(bar_containers) > 1:
        x_tick_data = sorted(
            [(lbl.get_position()[0], lbl.get_text()) for lbl in ax.get_xticklabels()],
            key=lambda t: t[0],
        )
        x_categories = [text for _, text in x_tick_data]

        groups: list[dict] = []
        for bc in bar_containers:
            y_sorted = sorted(
                [(c.get_x(), c.get_height()) for c in bc.get_children()],
                key=lambda t: t[0],
            )
            groups.append(
                {
                    "label": bc.get_label(),
                    "y": [float(v) for _, v in y_sorted],
                    "color": mcolors.to_hex(plt.getp(bc[0], "facecolor")),
                }
            )
        bars.append({"x_categories": x_categories, "groups": groups})

    # --- axis metadata ---
    xlabel = re.sub(r"\$(.+?)\$", r"\\q(\1)", ax.get_xlabel())
    ylabel = re.sub(r"\$(.+?)\$", r"\\q(\1)", ax.get_ylabel())

    legend = ax.get_legend()
    legend_title = ""
    if legend is not None:
        raw_title = legend.get_title().get_text() or ""
        legend_title = re.sub(r"\$(.+?)\$", r"\\q(\1)", raw_title)

    figsize = fig.get_size_inches()

    return {
        "plots": plots,
        "bars": bars,
        "xlabel": xlabel,
        "ylabel": ylabel,
        "xscale": ax.get_xscale(),
        "yscale": ax.get_yscale(),
        "xlim": list(ax.get_xlim()),
        "ylim": list(ax.get_ylim()),
        "figsize": [float(figsize[0]), float(figsize[1])],
        "legend_title": legend_title,
        "output_format": kwargs.get("output_format", "opju"),
        "pptx_layout": kwargs.get("pptx_layout", {"graphs_per_slide": 1}),
        "folder_name": kwargs.get("folder_name"),
        "workbook_name": kwargs.get("workbook_name", "Book"),
        "worksheet_name": kwargs.get("worksheet_name", "Sheet"),
        "graph_name": kwargs.get("graph_name", "Graph"),
    }


# ---------------------------------------------------------------------------
# HTTP transport helpers
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    if _BEARER_TOKEN:
        return {"Authorization": f"Bearer {_BEARER_TOKEN}"}
    return {}


def _poll_until_done(
    client: httpx.Client,
    server_url: str,
    job_id: str,
    interval: int = 3,
    timeout: int = 360,
) -> str:
    """Poll GET /job/{job_id} until a terminal status is reached.

    Returns the final status string.
    Raises TimeoutError if *timeout* seconds elapse without a terminal status.
    """
    elapsed = 0
    while elapsed < timeout:
        resp = client.get(f"{server_url}/job/{job_id}", headers=_headers())
        resp.raise_for_status()
        status: str = resp.json()["status"]
        if status in ("success", "failed", "timeout", "cancelled"):
            return status
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Polling timed out after {timeout}s waiting for job {job_id}.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(
    fig,
    ax,
    *args,
    server_url: str | None = None,
    output_path: str | None = None,
    verify: bool | str = False,
    **kwargs,
) -> str:
    """Send a matplotlib figure to matplotlib-to-originlab-server.

    Parameters
    ----------
    fig:
        matplotlib Figure object.
    ax:
        matplotlib Axes object.
    server_url:
        Override the server URL for this call only.
    output_path:
        Local path to write the downloaded result file.
        Defaults to ``"<graph_name>.<output_format>"`` in the working directory.
    verify:
        SSL verification.  ``False`` disables certificate checks (useful for
        self-signed certs on a LAN).  Pass a CA-bundle path to use a custom cert.
    **kwargs:
        Forwarded to the server as part of ``figure_data``:

        - ``folder_name``, ``workbook_name``, ``worksheet_name``, ``graph_name``
        - ``output_format``: ``"opju"`` (default) or ``"pptx"``
        - ``pptx_layout``: ``{"graphs_per_slide": 1}``

    Returns
    -------
    str
        Absolute path to the downloaded result file.

    Raises
    ------
    httpx.HTTPStatusError
        If the server returns an HTTP error response.
    RuntimeError
        If the job finishes with a non-success status.
    TimeoutError
        If polling exceeds the timeout (360 s by default).
    """
    url = (server_url or _SERVER_URL).rstrip("/")
    figure_data = _extract_figure_data(fig, ax, **kwargs)

    with httpx.Client(verify=verify) as client:
        # 1. Submit job
        resp = client.post(
            f"{url}/job",
            json={"figure_data": figure_data},
            headers=_headers(),
        )
        resp.raise_for_status()
        job_id: str = resp.json()["job_id"]

        # 2. Poll until done
        status = _poll_until_done(client, url, job_id)
        if status != "success":
            raise RuntimeError(
                f"Job {job_id} ended with status {status!r}. Check the server logs for details."
            )

        # 3. Download result
        resp = client.get(f"{url}/result/{job_id}", headers=_headers())
        resp.raise_for_status()

    if output_path is None:
        fmt = figure_data.get("output_format", "opju")
        graph_name = figure_data.get("graph_name", "Graph")
        output_path = f"{graph_name}.{fmt}"

    Path(output_path).write_bytes(resp.content)
    return str(Path(output_path).resolve())


def cancel(
    job_id: str,
    *,
    server_url: str | None = None,
    verify: bool | str = False,
) -> str:
    """Cancel a queued or running job on the server.

    Parameters
    ----------
    job_id:
        The job ID returned by a previous ``run()`` call (or obtained from
        ``POST /job``).
    server_url:
        Override the server URL for this call only.
    verify:
        SSL verification (same semantics as :func:`run`).

    Returns
    -------
    str
        The final status string as reported by the server (``"cancelled"``
        on success).

    Raises
    ------
    httpx.HTTPStatusError
        If the server returns an HTTP error (e.g. 404 job not found, 409
        already in a terminal state).
    """
    url = (server_url or _SERVER_URL).rstrip("/")
    with httpx.Client(verify=verify) as client:
        resp = client.post(f"{url}/job/{job_id}/cancel", headers=_headers())
        resp.raise_for_status()
    return resp.json().get("status", "cancelled")
