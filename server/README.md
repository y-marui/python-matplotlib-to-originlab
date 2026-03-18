# matplotlib-to-origin-server

Origin execution node for the matplotlib-to-origin ecosystem.

Install this on the machine that has OriginLab.  It accepts plot jobs from
[matplotlib-to-origin](../client/) clients running on any OS and executes
them locally using [matplotlib-to-origin-core](../core/).

> **Status:** Stub — implementation planned. See [ROADMAP.md](../ROADMAP.md).

## Requirements

- Windows
- OriginLab installed

## Installation

```bash
pip install matplotlib-to-origin-server
```

## Starting the server

```bash
matplotlib-to-origin-server --host 0.0.0.0 --port 8719
# or
python -m matplotlib_to_origin_server
```

## Client configuration

On the client machine, point matplotlib-to-origin at this server:

```python
from matplotlib_to_origin_remote import configure
configure("http://<server-ip>:8719")

import matplotlib_to_origin as mto
mto.run(fig, ax, mode="remote")
```

## Planned endpoints

| Method | Path       | Description                              |
|--------|------------|------------------------------------------|
| GET    | `/health`  | Server status and Origin availability    |
| GET    | `/version` | Server and core package versions         |
| POST   | `/run`     | Accept figure payload, execute in Origin |
