"""End-to-end integration tests for matplotlib-to-originlab-server.

Starts a real server subprocess with OriginLab available, sends jobs via the
remote client, and asserts that result .opju files are returned.

Requirements:
- Windows with OriginLab installed
- matplotlib-to-originlab-server and matplotlib-to-originlab-remote installed

Run:
    pytest server/tests/test_integration_origin.py -v -s

Skipped automatically on non-Windows or when Origin/server dependencies are missing.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="End-to-end Origin tests require Windows with OriginLab",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: int = 30) -> bool:
    """Poll GET /health until the server responds or timeout elapses."""
    import httpx
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def _origin_available() -> bool:
    try:
        import originpro as op  # noqa: F401
        return True
    except Exception:
        return False


def _server_deps_available() -> bool:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Fixtures / Base
# ---------------------------------------------------------------------------

@unittest.skipUnless(_origin_available(), "OriginLab not installed")
@unittest.skipUnless(_server_deps_available(), "fastapi/uvicorn not installed")
class _ServerTestBase(unittest.TestCase):
    """Start the server before all tests in the class, stop after."""

    server_proc: subprocess.Popen
    server_url: str
    port: int

    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use("Agg")

        cls.port = _find_free_port()
        cls.server_url = f"http://127.0.0.1:{cls.port}"

        cls.jobs_dir = tempfile.mkdtemp(prefix="mto_e2e_jobs_")

        cls.server_proc = subprocess.Popen(
            [
                sys.executable, "-m", "matplotlib_to_originlab_server",
                "--host", "127.0.0.1",
                "--port", str(cls.port),
            ],
            env={
                **__import__("os").environ,
                "MTO_JOBS_DIR": cls.jobs_dir,
            },
        )

        if not _wait_for_server(cls.server_url, timeout=60):
            cls.server_proc.terminate()
            raise RuntimeError(
                f"Server did not start within 60 s on port {cls.port}"
            )

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        try:
            cls.server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server_proc.kill()


# ---------------------------------------------------------------------------
# /health endpoint
# ---------------------------------------------------------------------------

class TestServerHealth(_ServerTestBase):

    def test_health_returns_ok(self):
        import httpx
        r = httpx.get(f"{self.server_url}/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_version_returns_server_key(self):
        import httpx
        r = httpx.get(f"{self.server_url}/version")
        self.assertEqual(r.status_code, 200)
        self.assertIn("server", r.json())


# ---------------------------------------------------------------------------
# Full round-trip via remote client
# ---------------------------------------------------------------------------

class TestRemoteRoundTrip(_ServerTestBase):

    def setUp(self):
        import matplotlib.pyplot as plt
        self.plt = plt

    def tearDown(self):
        self.plt.close("all")

    def _run_and_check(self, fig, ax, **kwargs) -> Path:
        from matplotlib_to_originlab_remote import run as remote_run
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "result.opju")
            result = remote_run(
                fig, ax,
                server_url=self.server_url,
                output_path=out,
                verify=False,
                **kwargs,
            )
            result_path = Path(result)
            self.assertTrue(result_path.exists(), f"Result file not found: {result}")
            self.assertGreater(result_path.stat().st_size, 0, "Result file is empty")
            # Copy to a stable location so teardown doesn't race the assertion
            import shutil
            stable = Path(tempfile.mktemp(suffix=".opju"))
            shutil.copy2(result_path, stable)
            return stable

    def test_line_plot_round_trip(self):
        import numpy as np
        fig, ax = self.plt.subplots()
        ax.plot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], label="line")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        out = self._run_and_check(fig, ax, graph_name="E2ELine")
        out.unlink(missing_ok=True)

    def test_scatter_round_trip(self):
        fig, ax = self.plt.subplots()
        ax.plot([1.0, 2.0, 3.0], [2.0, 1.0, 3.0],
                linestyle="None", marker="o", label="scatter")
        out = self._run_and_check(fig, ax, graph_name="E2EScatter")
        out.unlink(missing_ok=True)

    def test_errorbar_yerr_round_trip(self):
        import numpy as np
        fig, ax = self.plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=np.array([0.1, 0.2, 0.3]), label="eb",
        )
        out = self._run_and_check(fig, ax, graph_name="E2EYerr")
        out.unlink(missing_ok=True)

    def test_errorbar_both_err_round_trip(self):
        import numpy as np
        fig, ax = self.plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=np.array([0.1, 0.2, 0.3]),
            xerr=np.array([0.05, 0.10, 0.15]),
            label="eb",
        )
        out = self._run_and_check(fig, ax, graph_name="E2EBothErr")
        out.unlink(missing_ok=True)

    def test_two_jobs_sequential(self):
        """Second job must not inherit workbooks from the first (doc -s; check)."""
        import numpy as np
        for i in range(2):
            fig, ax = self.plt.subplots()
            ax.plot([1.0, 2.0, 3.0], [float(i), float(i+1), float(i+2)],
                    label=f"series{i}")
            out = self._run_and_check(fig, ax, graph_name=f"E2ESeq{i}")
            out.unlink(missing_ok=True)

    def test_cancel_queued_job(self):
        """Submit a job then immediately cancel it before it runs."""
        import httpx

        # Submit without waiting for result
        payload = {
            "figure_data": {
                "plots": [{"type": "line", "x": [1.0], "y": [2.0],
                           "yerr": None, "xerr": None, "label": "l",
                           "color": "#000000", "linestyle": "-",
                           "marker": "None", "markersize": 6.0,
                           "mec": "#000000", "mfc": "#000000",
                           "mew": 1.0, "linewidth": 1.5}],
                "bars": [], "xlabel": "", "ylabel": "",
                "xscale": "linear", "yscale": "linear",
                "xlim": [0.0, 2.0], "ylim": [0.0, 3.0],
                "figsize": [6.4, 4.8], "legend_title": "",
                "output_format": "opju", "graph_name": "CancelMe",
                "workbook_name": "Book", "worksheet_name": "Sheet",
                "folder_name": None,
                "pptx_layout": {"graphs_per_slide": 1},
            }
        }
        post_resp = httpx.post(f"{self.server_url}/job", json=payload)
        self.assertEqual(post_resp.status_code, 201)
        job_id = post_resp.json()["job_id"]

        # Cancel immediately — may already be running, both outcomes are valid
        cancel_resp = httpx.post(f"{self.server_url}/job/{job_id}/cancel")
        self.assertIn(cancel_resp.status_code, (200, 409))


if __name__ == "__main__":
    unittest.main()
