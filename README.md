# Matplotlib to Originlab

Convert matplotlib figures to OriginLab graphs — automatically choosing local
or remote execution depending on whether OriginLab is available.

---

## Monorepo structure

```
matplotlib-to-originlab/
├── core/      matplotlib-to-originlab-core    Local execution engine (Windows + Origin)
├── client/    matplotlib-to-originlab         User-facing client (all platforms)
├── remote/    matplotlib-to-originlab-remote  HTTP client for server mode
└── server/    matplotlib-to-originlab-server  Origin execution node
```

See each subdirectory for its own README and `pyproject.toml`.

---

## Quick start

Install the client (the only package most users need):

```bash
pip install matplotlib-to-originlab
```

Then:

```python
import matplotlib.pyplot as plt
import matplotlib_to_originlab as mto

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [4, 5, 6], label="sample")
ax.set_xlabel("X")
ax.set_ylabel("Y")
plt.legend()

mto.run(fig, ax)  # auto: local if Origin available, else remote
```

On a **Windows machine with OriginLab installed**, this uses Origin directly.
On **any other machine**, it forwards the job to a `matplotlib-to-originlab-server`
instance (configure the server URL with `matplotlib_to_originlab_remote.configure()`).

---

## Sample (matplotlib → Origin)

```python
import matplotlib.pyplot as plt
import matplotlib_to_originlab as mto
from astropy_extension.visualization import labeled_quantity_support
import astropy.units as u
import numpy as np

fig, ax = plt.subplots()

with labeled_quantity_support("$X$", "$M$"):
    xraw = np.linspace(-1, 1, 10)
    x = 10**xraw * u.m

    y = xraw * u.kg / u.s**2
    ax.plot(x, y, label="Model1")

    y = -xraw * 1e3 * u.g / u.s**2
    ax.plot(x, y, "o", markersize=10, label="Model2")

    yerr = np.array([0.1] * len(xraw)) * u.kg / u.s**2
    ax.errorbar(x, xraw * u.kg / u.s**2, fmt="o", yerr=yerr, label="Data", mfc="w")

    plt.xscale("log")
plt.legend()

mto.run(fig, ax, folder_name="Folder", workbook_name="Book", graph_name="Graph")
```

figure in python

![figure in python](sample/python.png)

graph in origin

![graph in origin](sample/origin.png)

---

## Architecture

```
[User Code]
    ↓
matplotlib-to-originlab  (client)
    ↓
┌──────────────────────────────────────┐
│  origin_available() == True          │
│    → matplotlib-to-originlab-core    │  (local, Windows + OriginLab)
│                                      │
│  origin_available() == False         │
│    → matplotlib-to-originlab-remote  │  (HTTP client)
└──────────────────────────────────────┘
    ↓ (remote path only)
matplotlib-to-originlab-server
    ↓
OriginLab
```

---

## Packages

| Package                           | Role                                  | Install via PyPI |
|-----------------------------------|---------------------------------------|-----------------|
| **matplotlib-to-originlab**       | User client — start here              | Planned          |
| matplotlib-to-originlab-core      | Local execution engine (Windows only) | No (path ref)    |
| matplotlib-to-originlab-remote    | HTTP client for server mode           | Planned          |
| matplotlib-to-originlab-server    | Origin execution node (Windows only)  | Planned          |

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full implementation plan, including:

- Remote transport implementation
- Server HTTP API
- Font size / axis label improvements in core
- `errorbar` `xerr` support
- PyPI publishing

---

## Origins

Forked from [jsbangsund/python_to_originlab](https://github.com/jsbangsund/python_to_originlab) (MIT).

Key changes from the fork:
- Switched from OriginEXT to `originpro`
- Added `astropy.units.Quantity` support
- Added `matplotlib.pyplot.errorbar` support (`yerr`)
- Restructured as a monorepo with client / core / remote / server separation

---

## License

MIT — see [LICENSE](LICENSE).
