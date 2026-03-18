"""matplotlib-to-origin-remote — HTTP client for matplotlib-to-origin-server.

This package is used automatically by matplotlib-to-origin when
origin_available() returns False.  It serialises the matplotlib figure and
sends it to a running matplotlib-to-origin-server instance.

NOTE: This module is a stub.  Full implementation is planned — see ROADMAP.md.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["run", "configure"]

# Default server endpoint.  Override with configure() or the
# MATPLOTLIB_TO_ORIGIN_SERVER_URL environment variable.
_SERVER_URL: str = "http://localhost:8719"


def configure(server_url: str) -> None:
    """Set the matplotlib-to-origin-server URL.

    Parameters
    ----------
    server_url:
        Base URL of the server, e.g. "http://192.168.1.10:8719".
    """
    global _SERVER_URL
    _SERVER_URL = server_url.rstrip("/")


def run(fig, ax, *args, server_url: str | None = None, **kwargs):
    """Send a matplotlib figure to matplotlib-to-origin-server.

    Parameters
    ----------
    fig:
        matplotlib Figure object.
    ax:
        matplotlib Axes object.
    server_url:
        Override the server URL for this call only.
    **kwargs:
        Additional options forwarded to the server.

    Raises
    ------
    NotImplementedError
        Until the remote transport is implemented (see ROADMAP.md).
    """
    # TODO: Implement serialisation and HTTP transport.
    # Planned implementation:
    #   1. Serialise fig/ax to a portable format (pickle + base64 or JSON).
    #   2. POST to {server_url}/run with the payload.
    #   3. Poll or await the job result.
    #   4. Return the result (e.g. path to the saved Origin project).
    raise NotImplementedError(
        "matplotlib-to-origin-remote is not yet implemented. "
        "See ROADMAP.md for the planned implementation. "
        "To use local Origin directly, install on a Windows machine with OriginLab "
        "or set mode='local' explicitly."
    )
