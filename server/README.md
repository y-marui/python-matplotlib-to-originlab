# matplotlib-to-originlab-server

Origin execution node for the Matplotlib to Originlab ecosystem.

Install this on the machine that has OriginLab.  It accepts plot jobs from
[matplotlib-to-originlab](../client/) clients running on any OS and executes
them locally using [matplotlib-to-originlab-core](../core/).

> **Status:** Stub — implementation planned. See [ROADMAP.md](../ROADMAP.md).

## Requirements

- Windows
- OriginLab installed

## Installation

```bash
pip install matplotlib-to-originlab-server
```

## Starting the server

```bash
matplotlib-to-originlab-server --host 0.0.0.0 --port 8719
# or
python -m matplotlib_to_originlab_server
```

## Client configuration

On the client machine, point matplotlib-to-originlab at this server:

```python
from matplotlib_to_originlab_remote import configure
configure("http://<server-ip>:8719")

import matplotlib_to_originlab as mto
mto.run(fig, ax, mode="remote")
```

## Planned endpoints

| Method | Path       | Description                              |
|--------|------------|------------------------------------------|
| GET    | `/health`  | Server status and Origin availability    |
| GET    | `/version` | Server and core package versions         |
| POST   | `/run`     | Accept figure payload, execute in Origin |
