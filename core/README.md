# matplotlib-to-originlab-core

Core execution engine for the Matplotlib to Originlab ecosystem.

**Not published to PyPI.** This package is referenced as a local path dependency by:
- `matplotlib-to-originlab` (client)
- `matplotlib-to-originlab-server`

## Requirements

- Windows
- OriginLab installed
- `originext`, `originpro`, `pywin32`

## Usage

This package is not meant to be imported directly by end users.
Use [`matplotlib-to-originlab`](../client/) instead.

```python
# Internal usage (via client)
from matplotlib_to_originlab_core import matplotlib_to_origin, numpy_to_origin
```

## API

- `matplotlib_to_origin(fig, ax, ...)` — Convert a matplotlib figure to an Origin graph
- `numpy_to_origin(data_array, ...)` — Send a numpy array to an Origin worksheet
- `connect_to_origin()` — Start/attach to an Origin session
- `createGraph_multiwks(...)` — Create a graph from multiple worksheets
