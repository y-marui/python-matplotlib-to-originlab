"""Tests for matplotlib-to-originlab-remote.

Covers:
- configure() / _headers()
- _extract_figure_data() — line, scatter, errorbar (yerr, xerr, both), bar
- _poll_until_done() — success, failed, timeout
- run() — happy path, job failure, polling timeout
- cancel() — success, 404 not found, 409 wrong state

Requires:
    pip install respx httpx matplotlib numpy pytest
    (astropy optional — astropy tests are skipped if not installed)

Run with:
    pytest remote/tests/test_remote.py
"""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch, MagicMock

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import httpx
import respx

import matplotlib_to_originlab_remote as remote
from matplotlib_to_originlab_remote import (
    cancel,
    configure,
    run,
    _extract_figure_data,
    _headers,
    _poll_until_done,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_fig():
    fig, ax = plt.subplots()
    return fig, ax


# ---------------------------------------------------------------------------
# configure() and _headers()
# ---------------------------------------------------------------------------

class TestConfigure(unittest.TestCase):

    def setUp(self):
        # Save originals
        self._orig_url = remote._SERVER_URL
        self._orig_token = remote._BEARER_TOKEN

    def tearDown(self):
        remote._SERVER_URL = self._orig_url
        remote._BEARER_TOKEN = self._orig_token

    def test_configure_server_url(self):
        configure(server_url="http://192.168.1.10:8719")
        self.assertEqual(remote._SERVER_URL, "http://192.168.1.10:8719")

    def test_configure_server_url_strips_trailing_slash(self):
        configure(server_url="http://192.168.1.10:8719/")
        self.assertEqual(remote._SERVER_URL, "http://192.168.1.10:8719")

    def test_configure_token(self):
        configure(token="secret123")
        self.assertEqual(remote._BEARER_TOKEN, "secret123")

    def test_configure_both(self):
        configure(server_url="http://host:9000", token="tok")
        self.assertEqual(remote._SERVER_URL, "http://host:9000")
        self.assertEqual(remote._BEARER_TOKEN, "tok")

    def test_configure_none_leaves_existing(self):
        configure(server_url="http://a:1")
        configure(server_url=None)
        self.assertEqual(remote._SERVER_URL, "http://a:1")

    def test_headers_no_token(self):
        remote._BEARER_TOKEN = None
        self.assertEqual(_headers(), {})

    def test_headers_with_token(self):
        remote._BEARER_TOKEN = "mytoken"
        self.assertEqual(_headers(), {"Authorization": "Bearer mytoken"})


# ---------------------------------------------------------------------------
# _extract_figure_data() — basic shapes
# ---------------------------------------------------------------------------

class TestExtractFigureDataLine(unittest.TestCase):

    def setUp(self):
        self.fig, self.ax = plt.subplots()
        self.ax.plot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], label="series1")

    def tearDown(self):
        plt.close(self.fig)

    def test_single_line_present(self):
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(len(data["plots"]), 1)

    def test_line_type(self):
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(data["plots"][0]["type"], "line")

    def test_x_y_values(self):
        data = _extract_figure_data(self.fig, self.ax)
        p = data["plots"][0]
        self.assertEqual(p["x"], [1.0, 2.0, 3.0])
        self.assertEqual(p["y"], [4.0, 5.0, 6.0])

    def test_label(self):
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(data["plots"][0]["label"], "series1")

    def test_no_err_fields(self):
        data = _extract_figure_data(self.fig, self.ax)
        p = data["plots"][0]
        self.assertIsNone(p["yerr"])
        self.assertIsNone(p["xerr"])

    def test_axes_metadata(self):
        self.ax.set_xlabel("X axis")
        self.ax.set_ylabel("Y axis")
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(data["xlabel"], "X axis")
        self.assertEqual(data["ylabel"], "Y axis")

    def test_output_format_default(self):
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(data["output_format"], "opju")

    def test_output_format_override(self):
        data = _extract_figure_data(self.fig, self.ax, output_format="pptx")
        self.assertEqual(data["output_format"], "pptx")


class TestExtractFigureDataScatter(unittest.TestCase):

    def setUp(self):
        self.fig, self.ax = plt.subplots()
        self.ax.plot([1.0, 2.0], [3.0, 4.0], linestyle="None", marker="o", label="pts")

    def tearDown(self):
        plt.close(self.fig)

    def test_scatter_type(self):
        data = _extract_figure_data(self.fig, self.ax)
        self.assertEqual(data["plots"][0]["type"], "scatter")


class TestExtractFigureDataErrorbar(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_yerr_only(self):
        fig, ax = plt.subplots()
        yerr = np.array([0.1, 0.2, 0.3])
        ax.errorbar([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], yerr=yerr, label="eb")
        data = _extract_figure_data(fig, ax)
        p = data["plots"][0]
        self.assertEqual(p["type"], "errorbar")
        np.testing.assert_allclose(p["yerr"], yerr.tolist(), atol=1e-10)
        self.assertIsNone(p["xerr"])

    def test_xerr_only(self):
        fig, ax = plt.subplots()
        xerr = np.array([0.05, 0.10, 0.15])
        ax.errorbar([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], xerr=xerr, label="eb")
        data = _extract_figure_data(fig, ax)
        p = data["plots"][0]
        self.assertEqual(p["type"], "errorbar")
        self.assertIsNone(p["yerr"])
        np.testing.assert_allclose(p["xerr"], xerr.tolist(), atol=1e-10)

    def test_both_err(self):
        fig, ax = plt.subplots()
        yerr = np.array([0.1, 0.2, 0.3])
        xerr = np.array([0.05, 0.10, 0.15])
        ax.errorbar([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], yerr=yerr, xerr=xerr, label="eb")
        data = _extract_figure_data(fig, ax)
        p = data["plots"][0]
        np.testing.assert_allclose(p["yerr"], yerr.tolist(), atol=1e-10)
        np.testing.assert_allclose(p["xerr"], xerr.tolist(), atol=1e-10)

    def test_label_extracted(self):
        fig, ax = plt.subplots()
        ax.errorbar([1.0, 2.0], [3.0, 4.0], yerr=[0.1, 0.2], label="my data")
        data = _extract_figure_data(fig, ax)
        self.assertEqual(data["plots"][0]["label"], "my data")

    def test_latex_label_converted(self):
        fig, ax = plt.subplots()
        ax.errorbar([1.0, 2.0], [3.0, 4.0], yerr=[0.1, 0.2], label="$\\alpha$")
        data = _extract_figure_data(fig, ax)
        self.assertEqual(data["plots"][0]["label"], r"\q(\alpha)")


class TestExtractFigureDataLatex(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_xlabel_latex(self):
        fig, ax = plt.subplots()
        ax.plot([1], [2])
        ax.set_xlabel("Time $t$ (s)")
        data = _extract_figure_data(fig, ax)
        self.assertEqual(data["xlabel"], r"Time \q(t) (s)")

    def test_ylabel_latex(self):
        fig, ax = plt.subplots()
        ax.plot([1], [2])
        ax.set_ylabel("$M/M_\\odot$")
        data = _extract_figure_data(fig, ax)
        self.assertEqual(data["ylabel"], r"\q(M/M_\odot)")


# ---------------------------------------------------------------------------
# _poll_until_done()
# ---------------------------------------------------------------------------

BASE = "http://localhost:8719"


class TestPollUntilDone(unittest.TestCase):

    @respx.mock
    def test_success_on_first_poll(self):
        respx.get(f"{BASE}/job/abc").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        with httpx.Client() as client:
            status = _poll_until_done(client, BASE, "abc", interval=0, timeout=10)
        self.assertEqual(status, "success")

    @respx.mock
    def test_polls_multiple_times_then_succeeds(self):
        responses = [
            httpx.Response(200, json={"status": "running"}),
            httpx.Response(200, json={"status": "running"}),
            httpx.Response(200, json={"status": "success"}),
        ]
        respx.get(f"{BASE}/job/xyz").mock(side_effect=responses)
        with httpx.Client() as client:
            with patch("time.sleep"):
                status = _poll_until_done(client, BASE, "xyz", interval=1, timeout=30)
        self.assertEqual(status, "success")

    @respx.mock
    def test_failed_status_returned(self):
        respx.get(f"{BASE}/job/fail").mock(
            return_value=httpx.Response(200, json={"status": "failed"})
        )
        with httpx.Client() as client:
            status = _poll_until_done(client, BASE, "fail", interval=0, timeout=10)
        self.assertEqual(status, "failed")

    @respx.mock
    def test_timeout_raises(self):
        respx.get(f"{BASE}/job/slow").mock(
            return_value=httpx.Response(200, json={"status": "running"})
        )
        with httpx.Client() as client:
            with patch("time.sleep"):
                with self.assertRaises(TimeoutError):
                    _poll_until_done(
                        client, BASE, "slow", interval=5, timeout=4
                    )


# ---------------------------------------------------------------------------
# run() — end-to-end with respx
# ---------------------------------------------------------------------------

class TestRun(unittest.TestCase):

    def setUp(self):
        self._orig_url = remote._SERVER_URL
        self._orig_token = remote._BEARER_TOKEN
        remote._SERVER_URL = BASE
        remote._BEARER_TOKEN = None

    def tearDown(self):
        remote._SERVER_URL = self._orig_url
        remote._BEARER_TOKEN = self._orig_token
        plt.close("all")

    @respx.mock
    def test_happy_path(self, tmp_path=None):
        import tempfile, os
        fake_bytes = b"PK fake opju content"

        respx.post(f"{BASE}/job").mock(
            return_value=httpx.Response(201, json={"job_id": "job-1"})
        )
        respx.get(f"{BASE}/job/job-1").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        respx.get(f"{BASE}/result/job-1").mock(
            return_value=httpx.Response(200, content=fake_bytes)
        )

        fig, ax = plt.subplots()
        ax.plot([1.0, 2.0], [3.0, 4.0], label="data")

        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "out.opju")
            result = run(fig, ax, output_path=out, graph_name="MyGraph")

        self.assertEqual(result, str(out) if os.path.isabs(out) else result)

    @respx.mock
    def test_job_failure_raises_runtime_error(self):
        respx.post(f"{BASE}/job").mock(
            return_value=httpx.Response(201, json={"job_id": "job-2"})
        )
        respx.get(f"{BASE}/job/job-2").mock(
            return_value=httpx.Response(200, json={"status": "failed"})
        )

        fig, ax = plt.subplots()
        ax.plot([1.0], [2.0])

        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError) as ctx:
                run(fig, ax, output_path=os.path.join(td, "out.opju"))
        self.assertIn("failed", str(ctx.exception))

    @respx.mock
    def test_bearer_token_sent(self):
        remote._BEARER_TOKEN = "test-secret"
        posted_headers: dict = {}

        def capture_post(request):
            posted_headers.update(dict(request.headers))
            return httpx.Response(201, json={"job_id": "job-3"})

        respx.post(f"{BASE}/job").mock(side_effect=capture_post)
        respx.get(f"{BASE}/job/job-3").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        respx.get(f"{BASE}/result/job-3").mock(
            return_value=httpx.Response(200, content=b"data")
        )

        fig, ax = plt.subplots()
        ax.plot([1.0], [2.0])

        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            run(fig, ax, output_path=os.path.join(td, "out.opju"))

        self.assertIn("authorization", posted_headers)
        self.assertEqual(posted_headers["authorization"], "Bearer test-secret")

    @respx.mock
    def test_output_path_default_naming(self):
        """Default output_path uses graph_name + output_format."""
        import tempfile, os
        fake_bytes = b"content"

        respx.post(f"{BASE}/job").mock(
            return_value=httpx.Response(201, json={"job_id": "job-4"})
        )
        respx.get(f"{BASE}/job/job-4").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        respx.get(f"{BASE}/result/job-4").mock(
            return_value=httpx.Response(200, content=fake_bytes)
        )

        fig, ax = plt.subplots()
        ax.plot([1.0], [2.0])

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            os.chdir(td)
            try:
                result = run(
                    fig, ax,
                    graph_name="MyGraph",
                    output_format="opju",
                )
            finally:
                os.chdir(cwd)
        self.assertTrue(result.endswith("MyGraph.opju"))


# ---------------------------------------------------------------------------
# cancel()
# ---------------------------------------------------------------------------

class TestCancel(unittest.TestCase):

    def setUp(self):
        self._orig_url = remote._SERVER_URL
        self._orig_token = remote._BEARER_TOKEN
        remote._SERVER_URL = BASE
        remote._BEARER_TOKEN = None

    def tearDown(self):
        remote._SERVER_URL = self._orig_url
        remote._BEARER_TOKEN = self._orig_token

    @respx.mock
    def test_cancel_queued_job(self):
        respx.post(f"{BASE}/job/job-q/cancel").mock(
            return_value=httpx.Response(200, json={"job_id": "job-q", "status": "cancelled"})
        )
        result = cancel("job-q")
        self.assertEqual(result, "cancelled")

    @respx.mock
    def test_cancel_running_job(self):
        respx.post(f"{BASE}/job/job-r/cancel").mock(
            return_value=httpx.Response(200, json={"job_id": "job-r", "status": "cancelled"})
        )
        result = cancel("job-r")
        self.assertEqual(result, "cancelled")

    @respx.mock
    def test_cancel_not_found_raises(self):
        respx.post(f"{BASE}/job/no-such/cancel").mock(
            return_value=httpx.Response(404, json={"detail": "Job not found"})
        )
        with self.assertRaises(httpx.HTTPStatusError):
            cancel("no-such")

    @respx.mock
    def test_cancel_terminal_state_raises(self):
        """409 is returned when the job is already in a terminal state."""
        respx.post(f"{BASE}/job/done-job/cancel").mock(
            return_value=httpx.Response(
                409, json={"detail": "Cannot cancel a job with status 'success'"}
            )
        )
        with self.assertRaises(httpx.HTTPStatusError):
            cancel("done-job")

    @respx.mock
    def test_cancel_sends_bearer_token(self):
        remote._BEARER_TOKEN = "cancel-token"
        sent_headers: dict = {}

        def capture(request):
            sent_headers.update(dict(request.headers))
            return httpx.Response(200, json={"job_id": "j", "status": "cancelled"})

        respx.post(f"{BASE}/job/j/cancel").mock(side_effect=capture)
        cancel("j")
        self.assertEqual(sent_headers.get("authorization"), "Bearer cancel-token")

    @respx.mock
    def test_cancel_server_url_override(self):
        alt = "http://alt-server:9000"
        respx.post(f"{alt}/job/job-x/cancel").mock(
            return_value=httpx.Response(200, json={"job_id": "job-x", "status": "cancelled"})
        )
        result = cancel("job-x", server_url=alt)
        self.assertEqual(result, "cancelled")


if __name__ == "__main__":
    unittest.main()
