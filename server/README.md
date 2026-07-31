# matplotlib-to-originlab-server

Origin execution node for the Matplotlib to Originlab ecosystem.

Install this on the machine that has OriginLab. It accepts plot jobs from
[matplotlib-to-originlab](../client/) clients running on any OS and executes
them locally using [matplotlib-to-originlab-core](../core/).

## Requirements

- Windows
- OriginLab installed

## Installation

```bash
pip install matplotlib-to-originlab-server
```

## Starting the server

```bash
# Minimal — listens on all interfaces, port 8719
matplotlib-to-originlab-server

# With HTTPS (recommended for remote access)
matplotlib-to-originlab-server \
    --ssl-certfile cert.pem \
    --ssl-keyfile  key.pem

# Restrict to specific clients
matplotlib-to-originlab-server --allow-ips "127.0.0.1,192.168.1.0/24"

# All options
matplotlib-to-originlab-server \
    --host 0.0.0.0 \
    --port 8719 \
    --ssl-certfile cert.pem \
    --ssl-keyfile  key.pem \
    --allow-ips "192.168.1.0/24"
```

## Environment variables

| Variable | Description |
|---|---|
| `MATPLOTLIB_TO_ORIGINLAB_TOKEN` | Bearer token required by all clients. Leave unset to disable auth. |
| `MATPLOTLIB_TO_ORIGINLAB_ALLOW_IPS` | Comma-separated IPs / CIDR networks allowed to connect. Leave unset to allow all. |
| `MATPLOTLIB_TO_ORIGINLAB_SERVER_URL` | *(client-side)* URL of this server. |
| `MTO_JOBS_DIR` | Directory for job files (default: `./jobs`). |
| `MTO_MAX_RUNTIME` | Per-job timeout in seconds (default: `300`). |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/job` | Submit a job, returns `job_id` |
| GET | `/job/{job_id}` | Poll job status |
| GET | `/result/{job_id}` | Download the result file |
| POST | `/job/{job_id}/cancel` | Cancel a queued or running job |
| GET | `/queue` | Inspect the full job queue |
| GET | `/health` | Liveness check |
| GET | `/version` | Package version info |

## Client configuration

On the client machine, point matplotlib-to-originlab at this server:

```python
from matplotlib_to_originlab_remote import configure

configure(server_url="https://<server-ip>:8719", token="your-token")

import matplotlib_to_originlab as mto

mto.run(fig, ax, mode="remote")
```

---

## Running as a Windows service

Use [NSSM (Non-Sucking Service Manager)](https://nssm.cc/) to register the
server as a Windows service so it starts automatically with the machine.

### 1. Install NSSM

Download from https://nssm.cc/download and place `nssm.exe` somewhere on
your `PATH` (e.g. `C:\tools\nssm.exe`).

### 2. Find the script path

```powershell
# Locate the installed entry point
(Get-Command matplotlib-to-originlab-server).Source
# Example output:
# C:\Users\user\AppData\Local\Programs\Python\Python311\Scripts\matplotlib-to-originlab-server.exe
```

### 3. Register the service

Open an **elevated** PowerShell or Command Prompt:

```powershell
nssm install MatplotlibToOriginlabServer "C:\...\matplotlib-to-originlab-server.exe"
nssm set MatplotlibToOriginlabServer AppParameters "--host 0.0.0.0 --port 8719"
nssm set MatplotlibToOriginlabServer AppEnvironmentExtra `
    "MATPLOTLIB_TO_ORIGINLAB_TOKEN=your-secret-token" `
    "MTO_JOBS_DIR=C:\mto-server\jobs"
nssm set MatplotlibToOriginlabServer AppDirectory "C:\mto-server"
nssm set MatplotlibToOriginlabServer Start SERVICE_AUTO_START
nssm start MatplotlibToOriginlabServer
```

### 4. Verify

```powershell
nssm status MatplotlibToOriginlabServer   # should show SERVICE_RUNNING
curl http://localhost:8719/health
```

### 5. Update / stop / remove

```powershell
nssm stop    MatplotlibToOriginlabServer
nssm restart MatplotlibToOriginlabServer
nssm remove  MatplotlibToOriginlabServer confirm
```

### Notes

- The service runs under the **Local System** account by default.
  OriginLab requires an interactive desktop session to operate its COM
  interface. Change the service account to a regular user account that is
  configured to auto-login, or run the service as **Local Service** with
  "Allow service to interact with desktop" enabled.
- Make sure the OriginLab licence is activated for the service account.
- Log output is written to `<AppDirectory>\jobs\<job_id>\log.txt` and to the
  NSSM log file (configure with `nssm set ... AppStdout / AppStderr`).
