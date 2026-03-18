# matplotlib-to-origin-remote

HTTP client for forwarding matplotlib figures to a
[matplotlib-to-origin-server](../server/) instance.

This package is used internally by
[matplotlib-to-origin](../client/) when `origin_available()` returns `False`.
You do not need to install it directly.

> **Status:** Stub — implementation planned. See [ROADMAP.md](../ROADMAP.md).

## Usage (via client)

```python
import matplotlib_to_origin as mto

# Remote mode is selected automatically when Origin is not available,
# or can be forced explicitly:
mto.run(fig, ax, mode="remote")
```

## Direct configuration

```python
from matplotlib_to_origin_remote import configure

configure("http://my-origin-server:8719")
```

## Planned transport

1. Serialise the matplotlib figure to a portable format.
2. POST to the server's `/run` endpoint.
3. Poll / await the result.
4. Return the saved Origin project path or status.
