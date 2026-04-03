"""Integration tests for matplotlib-to-originlab-server HTTP layer.

These tests spin up the FastAPI app via Starlette's TestClient and mock out
the db and worker modules so no OriginLab installation is needed.  They can
run on any OS (including Linux CI) and cover the full HTTP contract between
the server and a client.

Run with:
    pytest server/tests/test_app.py

Dependencies (no Origin required):
    pip install fastapi httpx starlette pytest
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Lazy import guard — skip if fastapi is not installed
# ---------------------------------------------------------------------------

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_job(
    job_id: str = "test-job-1",
    status: str = "queued",
    result_path: str | None = None,
    figure_data: str = "{}",
    error: str | None = None,
) -> dict:
    return {
        "id": job_id,
        "status": status,
        "created_at": _now(),
        "started_at": None,
        "finished_at": None,
        "figure_data": figure_data,
        "result_path": result_path,
        "error": error,
    }


# ---------------------------------------------------------------------------
# Base test class — patches db and worker at import time
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class _AppTestBase(unittest.TestCase):
    """Patches db and worker so the app can be imported without Origin."""

    def setUp(self):
        # We need to patch before importing app so that the module-level
        # `from . import db, worker` gets the mocked versions.
        self._db_patch = patch.dict("sys.modules", {
            "matplotlib_to_originlab_server.db": MagicMock(),
            "matplotlib_to_originlab_server.worker": MagicMock(),
        })
        self._db_patch.start()

        # Import (or re-use) app with patched deps
        import importlib
        import matplotlib_to_originlab_server.app as app_module
        importlib.reload(app_module)

        self.app_module = app_module
        self.db = app_module.db
        self.worker = app_module.worker
        self.client = TestClient(app_module.app, raise_server_exceptions=False)

    def tearDown(self):
        self._db_patch.stop()
        # Clear any env vars set during tests
        os.environ.pop("MATPLOTLIB_TO_ORIGINLAB_TOKEN", None)
        os.environ.pop("MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS", None)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth(_AppTestBase):

    def test_health_ok(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_health_has_auth_field(self):
        resp = self.client.get("/health")
        self.assertIn("auth", resp.json())

    def test_health_has_ip_allowlist_field(self):
        resp = self.client.get("/health")
        self.assertIn("ip_allowlist", resp.json())


# ---------------------------------------------------------------------------
# /version
# ---------------------------------------------------------------------------

class TestVersion(_AppTestBase):

    def test_version_returns_server_key(self):
        resp = self.client.get("/version")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("server", resp.json())


# ---------------------------------------------------------------------------
# POST /job
# ---------------------------------------------------------------------------

class TestSubmitJob(_AppTestBase):

    def test_submit_returns_201_and_job_id(self):
        self.db.create_job.return_value = None
        payload = {"figure_data": {"plots": [], "xlabel": "X", "ylabel": "Y"}}
        resp = self.client.post("/job", json=payload)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("job_id", resp.json())

    def test_submit_missing_figure_data_returns_422(self):
        resp = self.client.post("/job", json={})
        self.assertEqual(resp.status_code, 422)

    def test_submit_calls_db_create_job(self):
        self.db.create_job.return_value = None
        payload = {"figure_data": {"plots": []}}
        self.client.post("/job", json=payload)
        self.assertTrue(self.db.create_job.called)

    def test_submit_writes_input_json(self):
        self.db.create_job.return_value = None
        with tempfile.TemporaryDirectory() as td:
            self.app_module.JOBS_DIR = Path(td)
            payload = {"figure_data": {"plots": [], "graph_name": "G1"}}
            resp = self.client.post("/job", json=payload)
            job_id = resp.json()["job_id"]
            input_file = Path(td) / job_id / "input" / "figure_data.json"
            self.assertTrue(input_file.exists())
            data = json.loads(input_file.read_text())
            self.assertEqual(data["graph_name"], "G1")


# ---------------------------------------------------------------------------
# GET /job/{job_id}
# ---------------------------------------------------------------------------

class TestGetJobStatus(_AppTestBase):

    def test_get_existing_job(self):
        self.db.get_job.return_value = _make_job(status="running")
        resp = self.client.get("/job/test-job-1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "running")

    def test_get_missing_job_returns_404(self):
        self.db.get_job.return_value = None
        resp = self.client.get("/job/no-such-job")
        self.assertEqual(resp.status_code, 404)

    def test_get_job_returns_job_id(self):
        self.db.get_job.return_value = _make_job(job_id="abc", status="queued")
        resp = self.client.get("/job/abc")
        self.assertEqual(resp.json()["job_id"], "abc")


# ---------------------------------------------------------------------------
# GET /result/{job_id}
# ---------------------------------------------------------------------------

class TestGetResult(_AppTestBase):

    def test_result_job_not_found_returns_404(self):
        self.db.get_job.return_value = None
        resp = self.client.get("/result/no-such")
        self.assertEqual(resp.status_code, 404)

    def test_result_not_complete_returns_409(self):
        self.db.get_job.return_value = _make_job(status="running")
        resp = self.client.get("/result/test-job-1")
        self.assertEqual(resp.status_code, 409)

    def test_result_success_no_file_returns_404(self):
        self.db.get_job.return_value = _make_job(
            status="success", result_path="/nonexistent/result.opju"
        )
        resp = self.client.get("/result/test-job-1")
        self.assertEqual(resp.status_code, 404)

    def test_result_success_returns_file(self):
        with tempfile.NamedTemporaryFile(suffix=".opju", delete=False) as f:
            f.write(b"fake opju content")
            tmp_path = f.name
        try:
            self.db.get_job.return_value = _make_job(
                status="success", result_path=tmp_path
            )
            resp = self.client.get("/result/test-job-1")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content, b"fake opju content")
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# POST /job/{job_id}/cancel
# ---------------------------------------------------------------------------

class TestCancelJob(_AppTestBase):

    def test_cancel_not_found_returns_404(self):
        self.db.get_job.return_value = None
        resp = self.client.post("/job/no-such/cancel")
        self.assertEqual(resp.status_code, 404)

    def test_cancel_queued_job(self):
        self.db.get_job.return_value = _make_job(status="queued")
        self.db.update_job.return_value = None
        resp = self.client.post("/job/test-job-1/cancel")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "cancelled")

    def test_cancel_queued_calls_db_update(self):
        self.db.get_job.return_value = _make_job(job_id="q1", status="queued")
        self.db.update_job.return_value = None
        self.client.post("/job/q1/cancel")
        self.db.update_job.assert_called_once_with("q1", status="cancelled")

    def test_cancel_running_job(self):
        self.db.get_job.return_value = _make_job(status="running")
        self.db.update_job.return_value = None
        self.worker.force_restart_origin.return_value = None
        resp = self.client.post("/job/test-job-1/cancel")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "cancelled")

    def test_cancel_running_calls_force_restart(self):
        self.db.get_job.return_value = _make_job(job_id="r1", status="running")
        self.db.update_job.return_value = None
        self.worker.force_restart_origin.return_value = None
        self.client.post("/job/r1/cancel")
        self.assertTrue(self.worker.force_restart_origin.called)

    def test_cancel_terminal_job_returns_409(self):
        self.db.get_job.return_value = _make_job(status="success")
        resp = self.client.post("/job/test-job-1/cancel")
        self.assertEqual(resp.status_code, 409)

    def test_cancel_failed_job_returns_409(self):
        self.db.get_job.return_value = _make_job(status="failed")
        resp = self.client.post("/job/test-job-1/cancel")
        self.assertEqual(resp.status_code, 409)


# ---------------------------------------------------------------------------
# GET /queue
# ---------------------------------------------------------------------------

class TestGetQueue(_AppTestBase):

    def test_queue_returns_jobs_list(self):
        self.db.get_all_jobs.return_value = [
            _make_job("j1", "queued"),
            _make_job("j2", "success"),
        ]
        resp = self.client.get("/queue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("jobs", resp.json())
        self.assertEqual(len(resp.json()["jobs"]), 2)

    def test_queue_empty(self):
        self.db.get_all_jobs.return_value = []
        resp = self.client.get("/queue")
        self.assertEqual(resp.json()["jobs"], [])


# ---------------------------------------------------------------------------
# Bearer token middleware
# ---------------------------------------------------------------------------

class TestBearerTokenMiddleware(unittest.TestCase):

    @unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
    def test_unauthorized_without_token(self):
        os.environ["MATPLOTLIB_TO_ORIGINLAB_TOKEN"] = "secret"
        try:
            import importlib
            import matplotlib_to_originlab_server.app as app_module

            with patch.dict("sys.modules", {
                "matplotlib_to_originlab_server.db": MagicMock(),
                "matplotlib_to_originlab_server.worker": MagicMock(),
            }):
                importlib.reload(app_module)
                client = TestClient(app_module.app, raise_server_exceptions=False)
                resp = client.get("/health")
                self.assertEqual(resp.status_code, 401)
        finally:
            os.environ.pop("MATPLOTLIB_TO_ORIGINLAB_TOKEN", None)

    @unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
    def test_authorized_with_correct_token(self):
        os.environ["MATPLOTLIB_TO_ORIGINLAB_TOKEN"] = "secret"
        try:
            import importlib
            import matplotlib_to_originlab_server.app as app_module

            with patch.dict("sys.modules", {
                "matplotlib_to_originlab_server.db": MagicMock(),
                "matplotlib_to_originlab_server.worker": MagicMock(),
            }):
                importlib.reload(app_module)
                client = TestClient(app_module.app, raise_server_exceptions=False)
                resp = client.get("/health", headers={"Authorization": "Bearer secret"})
                self.assertEqual(resp.status_code, 200)
        finally:
            os.environ.pop("MATPLOTLIB_TO_ORIGINLAB_TOKEN", None)


if __name__ == "__main__":
    unittest.main()
