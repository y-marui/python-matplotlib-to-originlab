"""Integration tests for matplotlib-to-originlab-core — require OriginLab.

These tests call matplotlib_to_origin() with a real Origin session and verify
that the output .opju file is created and non-empty.

Skip automatically on non-Windows or when OriginLab is not installed:
    pytest core/tests/test_integration_origin.py

Run explicitly (CI with self-hosted Windows runner):
    pytest core/tests/test_integration_origin.py -m origin
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

# Skip every test in this module when not on Windows or Origin unavailable.
pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="OriginLab integration tests require Windows",
)


def _origin_available() -> bool:
    try:
        import originpro as op  # noqa: F401
        return True
    except Exception:
        return False


def _save_and_check(fig, ax, **kwargs):
    """Call matplotlib_to_origin, save with LabTalk, return (path, exists, size)."""
    import originpro as op
    from matplotlib_to_originlab_core import matplotlib_to_origin

    td = tempfile.mkdtemp()
    result_stem = str(Path(td) / "result")
    matplotlib_to_origin(fig, ax, **kwargs)
    op.lt_exec(f"save {result_stem};")
    result_path = Path(f"{result_stem}.opju")
    exists = result_path.exists()
    size = result_path.stat().st_size if exists else 0
    return result_path, exists, size


@unittest.skipUnless(_origin_available(), "originpro not installed or Origin unavailable")
class TestCoreLineplot(unittest.TestCase):

    def setUp(self):
        self.fig, self.ax = plt.subplots()

    def tearDown(self):
        plt.close(self.fig)

    def test_line_plot_creates_opju(self):
        self.ax.plot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], label="line1")
        _, exists, size = _save_and_check(
            self.fig, self.ax,
            workbook_name="TestBook",
            worksheet_name="TestSheet",
            graph_name="TestGraph",
        )
        self.assertTrue(exists, "Expected .opju file to be created")
        self.assertGreater(size, 0, "Expected .opju file to be non-empty")

    def test_scatter_plot_creates_opju(self):
        self.ax.plot(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            linestyle="None", marker="o", label="scatter1",
        )
        _, exists, size = _save_and_check(
            self.fig, self.ax,
            workbook_name="TestBook2",
            graph_name="TestGraph2",
        )
        self.assertTrue(exists)
        self.assertGreater(size, 0)

    def test_xlabel_ylabel_set(self):
        """Verify the call doesn't raise with non-trivial axis labels."""
        self.ax.plot([1.0, 2.0], [3.0, 4.0], label="data")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude")
        _, exists, _ = _save_and_check(
            self.fig, self.ax,
            graph_name="TestGraphLabels",
        )
        self.assertTrue(exists)

    def test_latex_labels(self):
        self.ax.plot([1.0, 2.0], [3.0, 4.0], label=r"$\alpha$")
        self.ax.set_xlabel(r"Time $t$ (s)")
        self.ax.set_ylabel(r"$M/M_\odot$")
        _, exists, _ = _save_and_check(
            self.fig, self.ax,
            graph_name="TestGraphLatex",
        )
        self.assertTrue(exists)

    def test_log_scale(self):
        x = np.logspace(0, 2, 10)
        self.ax.plot(x, x ** 2, label="power")
        self.ax.set_xscale("log")
        self.ax.set_yscale("log")
        _, exists, _ = _save_and_check(
            self.fig, self.ax,
            graph_name="TestGraphLog",
        )
        self.assertTrue(exists)


@unittest.skipUnless(_origin_available(), "originpro not installed or Origin unavailable")
class TestCoreErrorbar(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_errorbar_yerr(self):
        fig, ax = plt.subplots()
        yerr = np.array([0.1, 0.2, 0.3])
        ax.errorbar([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], yerr=yerr, label="eb")
        _, exists, size = _save_and_check(fig, ax, graph_name="TestEbYerr")
        self.assertTrue(exists)
        self.assertGreater(size, 0)

    def test_errorbar_xerr(self):
        fig, ax = plt.subplots()
        xerr = np.array([0.05, 0.10, 0.15])
        ax.errorbar([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], xerr=xerr, label="eb")
        _, exists, _ = _save_and_check(fig, ax, graph_name="TestEbXerr")
        self.assertTrue(exists)

    def test_errorbar_both(self):
        fig, ax = plt.subplots()
        yerr = np.array([0.1, 0.2, 0.3])
        xerr = np.array([0.05, 0.10, 0.15])
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=yerr, xerr=xerr, label="eb",
        )
        _, exists, _ = _save_and_check(fig, ax, graph_name="TestEbBoth")
        self.assertTrue(exists)

    def test_errorbar_no_capsize(self):
        fig, ax = plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=[0.1, 0.2, 0.3], capsize=0, label="eb",
        )
        _, exists, _ = _save_and_check(fig, ax, graph_name="TestEbNoCap")
        self.assertTrue(exists)


@unittest.skipUnless(_origin_available(), "originpro not installed or Origin unavailable")
class TestCoreMultipleSeries(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_multiple_lines(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3], label="A")
        ax.plot([1, 2, 3], [3, 2, 1], label="B")
        ax.legend()
        _, exists, _ = _save_and_check(fig, ax, graph_name="TestMultiLine")
        self.assertTrue(exists)

    def test_mixed_line_and_scatter(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9], label="curve")
        ax.plot([1, 2, 3], [2, 3, 5], linestyle="None", marker="^", label="pts")
        _, exists, _ = _save_and_check(fig, ax, graph_name="TestMixed")
        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
