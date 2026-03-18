"""matplotlib-to-origin — unified client for converting matplotlib figures to OriginLab.

Usage
-----
import matplotlib_to_origin as mto

mto.run(fig, ax)                     # auto mode (default)
mto.run(fig, ax, mode="local")       # force local Origin execution
mto.run(fig, ax, mode="remote")      # force remote server execution

Execution strategy
------------------
mode="auto"  (default):
    origin_available() == True  → local via matplotlib-to-origin-core
    origin_available() == False → remote via matplotlib-to-origin-remote

mode="local":
    Always use local Origin (fails if Origin is not available)

mode="remote":
    Always send to matplotlib-to-origin-server
"""

from __future__ import annotations

from functools import lru_cache

__version__ = "0.1.0"

__all__ = ["run", "matplotlib_to_origin", "origin_available"]


@lru_cache(maxsize=1)
def origin_available() -> bool:
    """Return True if OriginLab is accessible on this machine.

    The result is cached for the lifetime of the process to avoid
    repeatedly launching Origin.
    """
    try:
        import win32com.client
        win32com.client.Dispatch("Origin.Application")
        return True
    except Exception:
        return False


def run(fig, ax, *args, mode: str = "auto", **kwargs):
    """Convert a matplotlib figure to an OriginLab graph.

    Parameters
    ----------
    fig:
        matplotlib Figure object.
    ax:
        matplotlib Axes object.
    mode : {"auto", "local", "remote"}, default "auto"
        Execution strategy.
        - "auto"   : use local if Origin is available, else remote.
        - "local"  : force local execution (requires OriginLab on Windows).
        - "remote" : forward to matplotlib-to-origin-server.
    **kwargs:
        Forwarded to the underlying execution backend.
        See matplotlib_to_origin_core.matplotlib_to_origin for local options.
        See matplotlib_to_origin_remote.run for remote options.
    """
    if mode == "auto":
        use_local = origin_available()
    elif mode == "local":
        use_local = True
    elif mode == "remote":
        use_local = False
    else:
        raise ValueError(
            f"Unknown mode: {mode!r}. Choose from 'auto', 'local', or 'remote'."
        )

    if use_local:
        from matplotlib_to_origin_core import matplotlib_to_origin as _local
        return _local(fig, ax, *args, **kwargs)
    else:
        from matplotlib_to_origin_remote import run as _remote
        return _remote(fig, ax, *args, **kwargs)


# Convenience alias for users who prefer the long-form name
matplotlib_to_origin = run
