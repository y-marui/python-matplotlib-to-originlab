# matplotlib-to-origin-core

Core execution engine for the matplotlib-to-origin ecosystem.

**Not published to PyPI.** This package is referenced as a local path dependency by:
- `matplotlib-to-origin` (client)
- `matplotlib-to-origin-server`

## Requirements

- Windows
- OriginLab installed
- `originext`, `originpro`, `pywin32`

## Usage

This package is not meant to be imported directly by end users.
Use [`matplotlib-to-origin`](../client/) instead.

```python
# Internal usage (via client)
from matplotlib_to_origin_core import matplotlib_to_origin, numpy_to_origin
```

## API

- `matplotlib_to_origin(fig, ax, ...)` — Convert a matplotlib figure to an Origin graph
- `numpy_to_origin(data_array, ...)` — Send a numpy array to an Origin worksheet
- `connect_to_origin()` — Start/attach to an Origin session
- `createGraph_multiwks(...)` — Create a graph from multiple worksheets
