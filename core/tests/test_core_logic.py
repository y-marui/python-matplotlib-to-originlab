"""Tests for matplotlib-to-originlab-core logic that do not require OriginLab.

These tests cover pure-Python and pure-matplotlib behaviour:
- Data extraction from ErrorbarContainer (yerr and xerr)
- Font size extraction from matplotlib axes
- LaTeX → LabTalk label conversion

Origin-dependent code paths (matplotlib_to_origin, numpy_to_origin) are
tested only in integration tests that require a Windows machine with OriginLab.

Run with:
    pytest core/tests/test_core_logic.py
"""

import re
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _latex_to_labtalk(text: str) -> str:
    """Replicate the regex used in the core to convert LaTeX to LabTalk."""
    return re.sub(r"\$(.+?)\$", r"\\q(\1)", text)


# ---------------------------------------------------------------------------
# ErrorbarContainer — yerr extraction
# ---------------------------------------------------------------------------

class TestYerrExtraction(unittest.TestCase):
    """barlinecols approach for yerr (works for any capsize)."""

    def _make_ax(self, yerr, capsize=5):
        fig, ax = plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=yerr, capsize=capsize, label="data",
        )
        self._fig = fig
        return ax

    def tearDown(self):
        plt.close(self._fig)

    def test_symmetric_yerr(self):
        yerr_vals = np.array([0.1, 0.2, 0.3])
        ax = self._make_ax(yerr=yerr_vals)

        from matplotlib.container import ErrorbarContainer
        c = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))
        self.assertTrue(c.has_yerr)

        segs = c.lines[2][0].get_segments()
        extracted = np.array([(s[1][1] - s[0][1]) / 2 for s in segs])
        np.testing.assert_allclose(extracted, yerr_vals, atol=1e-10)

    def test_yerr_no_capsize(self):
        """barlinecols must work even when capsize=0 (no cap markers)."""
        yerr_vals = np.array([0.1, 0.2, 0.3])
        ax = self._make_ax(yerr=yerr_vals, capsize=0)

        from matplotlib.container import ErrorbarContainer
        c = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))

        segs = c.lines[2][0].get_segments()
        extracted = np.array([(s[1][1] - s[0][1]) / 2 for s in segs])
        np.testing.assert_allclose(extracted, yerr_vals, atol=1e-10)


# ---------------------------------------------------------------------------
# ErrorbarContainer — xerr extraction
# ---------------------------------------------------------------------------

class TestXerrExtraction(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_symmetric_xerr(self):
        xerr_vals = np.array([0.05, 0.10, 0.15])
        fig, ax = plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            xerr=xerr_vals, capsize=5, label="data",
        )

        from matplotlib.container import ErrorbarContainer
        c = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))
        self.assertFalse(c.has_yerr)
        self.assertTrue(c.has_xerr)

        segs = c.lines[2][0].get_segments()
        extracted = np.array([(s[1][0] - s[0][0]) / 2 for s in segs])
        np.testing.assert_allclose(extracted, xerr_vals, atol=1e-10)

    def test_both_yerr_and_xerr(self):
        """matplotlib stores barcols in order: xerr first, then yerr."""
        yerr_vals = np.array([0.1, 0.2, 0.3])
        xerr_vals = np.array([0.05, 0.10, 0.15])
        fig, ax = plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            yerr=yerr_vals, xerr=xerr_vals, capsize=5, label="data",
        )

        from matplotlib.container import ErrorbarContainer
        c = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))
        self.assertTrue(c.has_yerr)
        self.assertTrue(c.has_xerr)

        # barcols[0] = xerr (horizontal), barcols[1] = yerr (vertical)
        x_segs = c.lines[2][0].get_segments()
        y_segs = c.lines[2][1].get_segments()

        extracted_xerr = np.array([(s[1][0] - s[0][0]) / 2 for s in x_segs])
        extracted_yerr = np.array([(s[1][1] - s[0][1]) / 2 for s in y_segs])

        np.testing.assert_allclose(extracted_xerr, xerr_vals, atol=1e-10)
        np.testing.assert_allclose(extracted_yerr, yerr_vals, atol=1e-10)

    def test_xerr_no_capsize(self):
        xerr_vals = np.array([0.05, 0.10, 0.15])
        fig, ax = plt.subplots()
        ax.errorbar(
            [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
            xerr=xerr_vals, capsize=0, label="data",
        )

        from matplotlib.container import ErrorbarContainer
        c = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))

        segs = c.lines[2][0].get_segments()
        extracted = np.array([(s[1][0] - s[0][0]) / 2 for s in segs])
        np.testing.assert_allclose(extracted, xerr_vals, atol=1e-10)


# ---------------------------------------------------------------------------
# Font size extraction
# ---------------------------------------------------------------------------

class TestFontSizeExtraction(unittest.TestCase):

    def setUp(self):
        self.fig, self.ax = plt.subplots()
        self.ax.plot([1, 2, 3], [4, 5, 6])
        self.ax.set_xlabel("X label", fontsize=14)
        self.ax.set_ylabel("Y label", fontsize=16)
        self.ax.tick_params(axis="x", labelsize=11)
        self.ax.tick_params(axis="y", labelsize=12)

    def tearDown(self):
        plt.close(self.fig)

    def test_axis_title_fontsize(self):
        self.assertEqual(self.ax.xaxis.label.get_fontsize(), 14)
        self.assertEqual(self.ax.yaxis.label.get_fontsize(), 16)

    def test_tick_label_fontsize(self):
        self.fig.canvas.draw()  # force tick label rendering
        x_ticks = self.ax.xaxis.get_ticklabels()
        y_ticks = self.ax.yaxis.get_ticklabels()
        if x_ticks:
            self.assertEqual(x_ticks[0].get_fontsize(), 11)
        if y_ticks:
            self.assertEqual(y_ticks[0].get_fontsize(), 12)

    def test_legend_text_fontsize(self):
        self.ax.plot([1, 2, 3], [6, 5, 4], label="line2")
        self.ax.legend(fontsize=13)
        legend = self.ax.get_legend()
        self.assertIsNotNone(legend)
        texts = legend.get_texts()
        self.assertTrue(len(texts) > 0)
        self.assertEqual(texts[0].get_fontsize(), 13)

    def test_legend_title_text(self):
        self.ax.plot([1, 2, 3], [6, 5, 4], label="line2")
        self.ax.legend(title="My legend")
        legend = self.ax.get_legend()
        self.assertEqual(legend.get_title().get_text(), "My legend")


# ---------------------------------------------------------------------------
# LaTeX → LabTalk label conversion
# ---------------------------------------------------------------------------

class TestLatexToLabtalk(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(_latex_to_labtalk("$X$"), r"\q(X)")

    def test_mixed(self):
        self.assertEqual(_latex_to_labtalk("Time $t$ (s)"), r"Time \q(t) (s)")

    def test_no_latex(self):
        self.assertEqual(_latex_to_labtalk("Plain text"), "Plain text")

    def test_multiple(self):
        self.assertEqual(
            _latex_to_labtalk("$M$ vs $X$"),
            r"\q(M) vs \q(X)",
        )

    def test_complex_expression(self):
        self.assertEqual(
            _latex_to_labtalk(r"Mass $M/M_\odot$"),
            r"Mass \q(M/M_\odot)",
        )


# ---------------------------------------------------------------------------
# Astropy units helpers  (skipped if astropy is not installed)
# ---------------------------------------------------------------------------

try:
    import astropy.units as u
    HAS_ASTROPY = True
except ImportError:
    HAS_ASTROPY = False


def _unit_str(unit) -> str:
    """Mirror of the helper in the core module."""
    if unit is None:
        return ''
    try:
        return unit.to_string()
    except AttributeError:
        return str(unit)


def _strip_unit(v) -> float:
    """Mirror of the helper in the core module."""
    return float(v.value) if hasattr(v, "value") else float(v)


@unittest.skipUnless(HAS_ASTROPY, "astropy not installed")
class TestUnitHelpers(unittest.TestCase):

    def test_unit_str_none(self):
        self.assertEqual(_unit_str(None), '')

    def test_unit_str_meter(self):
        self.assertEqual(_unit_str(u.m), 'm')

    def test_unit_str_compound(self):
        unit = u.kg / u.s**2
        result = _unit_str(unit)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_strip_unit_quantity(self):
        q = 3.14 * u.m
        self.assertAlmostEqual(_strip_unit(q), 3.14)

    def test_strip_unit_plain_float(self):
        self.assertAlmostEqual(_strip_unit(2.71), 2.71)

    def test_strip_unit_xlim(self):
        """ax.get_xlim() with astropy should survive _strip_unit."""
        fig, ax = plt.subplots()
        ax.set_xlim(0.0, 10.0)
        lo, hi = (_strip_unit(v) for v in ax.get_xlim())
        self.assertAlmostEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 10.0)
        plt.close(fig)


@unittest.skipUnless(HAS_ASTROPY, "astropy not installed")
class TestAstropyDataExtraction(unittest.TestCase):
    """Verify that Quantity x/y data is correctly stripped before passing to Origin."""

    def test_quantity_xdata_strip(self):
        x = np.array([1.0, 2.0, 3.0]) * u.m
        # Simulate what the core does
        extracted = np.float64(x.value).tolist()
        self.assertEqual(extracted, [1.0, 2.0, 3.0])

    def test_unit_propagation(self):
        """Units from ax.xaxis / yaxis should survive _unit_str."""
        fig, ax = plt.subplots()
        try:
            from astropy.visualization import quantity_support
            with quantity_support():
                ax.plot([1, 2, 3] * u.m, [4, 5, 6] * u.kg)
                x_unit = ax.xaxis.get_units()
                y_unit = ax.yaxis.get_units()
                if x_unit is not None:
                    self.assertIn('m', _unit_str(x_unit))
                if y_unit is not None:
                    self.assertIn('kg', _unit_str(y_unit))
        finally:
            plt.close(fig)


if __name__ == "__main__":
    unittest.main()
