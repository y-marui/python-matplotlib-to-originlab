# matplotlib-to-originlab

Unified client for converting matplotlib figures to OriginLab graphs.

This is the **only package end users need to install**.

## Installation

```bash
pip install matplotlib-to-originlab
```

## Usage

```python
import matplotlib.pyplot as plt
import matplotlib_to_originlab as mto

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [4, 5, 6], label="sample")
ax.set_xlabel("X")
ax.set_ylabel("Y")

# Auto mode: uses local Origin if available, otherwise forwards to server
mto.run(fig, ax)

# Explicit mode selection
mto.run(fig, ax, mode="local")   # requires OriginLab on this machine
mto.run(fig, ax, mode="remote")  # always use matplotlib-to-originlab-server
```

## Execution Strategy

```
origin_available() == True  → matplotlib-to-originlab-core  (local, Windows + Origin)
origin_available() == False → matplotlib-to-originlab-remote (HTTP client → server)
```

`origin_available()` checks whether OriginLab can be launched via COM on the
current machine. The result is cached for the process lifetime.

## Architecture

```
[User Code]
    ↓
matplotlib-to-originlab  (this package)
    ↓
┌─────────────────────────────────────────┐
│  origin_available() == True             │
│    → matplotlib-to-originlab-core       │
│                                         │
│  origin_available() == False            │
│    → matplotlib-to-originlab-remote     │
└─────────────────────────────────────────┘
    ↓
[matplotlib-to-originlab-server]
    ↓
[OriginLab]
```

## Related Packages

| Package                           | Role                        |
|-----------------------------------|-----------------------------|
| **matplotlib-to-originlab**       | This package — user client  |
| matplotlib-to-originlab-core      | Local execution engine      |
| matplotlib-to-originlab-remote    | HTTP client for server mode |
| matplotlib-to-originlab-server    | Origin execution node       |
