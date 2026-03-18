"""HTTP server for matplotlib-to-origin-server.

Planned stack: FastAPI + uvicorn (Windows, with OriginLab installed).

NOTE: This module is a stub.  Full implementation is planned — see ROADMAP.md.

Planned endpoints
-----------------
POST /run
    Accept a serialised matplotlib figure, execute via matplotlib-to-origin-core,
    and return the result (e.g. saved Origin project path).

GET /health
    Return server status and Origin availability.

GET /version
    Return server and core package versions.
"""

from __future__ import annotations

# TODO: Implement FastAPI application.
# Example skeleton (requires: pip install fastapi uvicorn):
#
# from fastapi import FastAPI
# from matplotlib_to_origin_core import matplotlib_to_origin
#
# app = FastAPI(title="matplotlib-to-origin-server")
#
# @app.get("/health")
# def health():
#     return {"status": "ok", "origin_available": True}
#
# @app.post("/run")
# def run_job(payload: dict):
#     # 1. Deserialise the figure from payload
#     # 2. Call matplotlib_to_origin(fig, ax, ...)
#     # 3. Return result
#     raise NotImplementedError
#
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8719)


def main() -> None:
    raise NotImplementedError(
        "matplotlib-to-origin-server is not yet implemented. "
        "See ROADMAP.md for the planned implementation."
    )


if __name__ == "__main__":
    main()
