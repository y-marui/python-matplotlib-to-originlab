"""matplotlib-to-originlab-server — Origin execution node.

Receives plot jobs from matplotlib-to-originlab-remote clients,
executes them using matplotlib-to-originlab-core (OriginLab), and
returns the results.

NOTE: This module is a stub.  Full implementation is planned — see ROADMAP.md.

Start the server
----------------
    python -m matplotlib_to_originlab_server
    # or
    matplotlib-to-originlab-server --host 0.0.0.0 --port 8719
"""

from __future__ import annotations

__version__ = "0.1.0"
