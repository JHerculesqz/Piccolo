# Piccolo

**Turn any Windows, Linux, or macOS PC or server into a browser-accessible cloud computer on your LAN — and give your AI Agents a real machine to work on.**

[English](README.md) · [简体中文](docs/README_zh.md)

Piccolo is a lightweight microservice that publishes an existing VNC desktop ([TigerVNC](https://tigervnc.org/)) to the web through [noVNC](https://github.com/novnc/noVNC). No agent runtime, no container sandbox, no heavyweight orchestration — just your machine, your desktop, and a URL.

## Table of Contents

- [What is Piccolo?](#what-is-piccolo)
- [Why Piccolo?](#why-piccolo)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Option 1: Run with uv](#option-1-run-with-uv)
  - [Option 2: Run with Docker Compose](#option-2-run-with-docker-compose)
  - [Open the Desktop](#open-the-desktop)
- [Use Cases](#use-cases)
- [Security Notes](#security-notes)
- [Goals](#goals)
- [Documentation](#documentation)
- [License](#license)

## What is Piccolo?

Piccolo turns a personal PC or server — Windows, Linux, or macOS — into a **cloud computer inside your local network**. It exposes the machine's VNC desktop through a web page, so any device with a browser can see and control it.

In practice, Piccolo is the missing link between an AI Agent and the desktop software it needs to operate:

- The host keeps running TigerVNC and its normal desktop session.
- Piccolo serves the noVNC client and bridges the browser's WebSocket connection to the VNC server.
- The desktop becomes available at a single LAN URL: `http://<host-ip>:65211/vnc.html?autoconnect=true`.
- An Agent (or a person) can then open applications, click, type, and complete real work — with no client software to install on the viewing device.

### At a glance

| Property | Value |
| --- | --- |
| Input | An existing TigerVNC server on a Windows / Linux / macOS host |
| Output | A noVNC web desktop on your LAN |
| Default web port | `65211` |
| Deployment | `uv run` or Docker Compose |
| Client requirement | A modern browser |

## Why Piccolo?

The agent ecosystem is full of sandbox middleware, and projects such as **E2B** and **OpenSandbox** are excellent at what they do. But they are general-purpose and, for this job, too heavy — and more importantly, they solve a different problem.

The software an Agent must operate often **cannot fit inside a small sandbox at all**:

- **Ansys, ANSA, Cadence**, and other CAD / CAE / EDA tools require workstation-class CPUs, large amounts of memory, GPUs, and licensed desktop installations.
- These applications expect a full desktop environment, not a stripped-down container.
- The hardware that runs them is usually a real personal workstation or server that already exists.

Piccolo takes the opposite approach: instead of moving the workload into a sandbox, it **brings the browser to the machine that already has the software**.

| | Container sandboxes (E2B, OpenSandbox, ...) | Piccolo |
| --- | --- | --- |
| Unit of execution | Container | Existing PC or server |
| Best for | Untrusted code, short-lived tasks | Heavy desktop software: CAD, CAE, EDA, ... |
| Resource ceiling | Limited by the container | The full machine |
| Setup cost | Image build and sandbox orchestration | Install TigerVNC, start Piccolo |
| Access | SDK / API | Any browser via noVNC |

Piccolo is not a replacement for sandboxes. It is the complement: use a sandbox for isolated code execution, and use Piccolo when the Agent needs the real desktop and the real software.

## How It Works

```
┌─────────────────────────┐     HTTP + WebSocket      ┌─────────────────────────┐
│  Browser / Agent UI     │ ────────────────────────▶ │  Piccolo                │
│  noVNC client           │ ◀──────────────────────── │  :65211                 │
└─────────────────────────┘                           └────────────┬────────────┘
                                                                   │ RFB over TCP
                                                                   ▼
                                                      ┌─────────────────────────┐
                                                      │  TigerVNC               │
                                                      │  :65212 (example)       │
                                                      └────────────┬────────────┘
                                                                   ▼
                                                      ┌─────────────────────────┐
                                                      │  Host desktop session   │
                                                      │  Windows / Linux / macOS│
                                                      └─────────────────────────┘
```

1. The browser loads the noVNC web client from Piccolo.
2. noVNC opens a WebSocket connection back to Piccolo.
3. Piccolo forwards the session to the TigerVNC server over RFB.
4. The TigerVNC server exposes the host's real desktop.

## Quick Start

### Prerequisites

- **TigerVNC** is installed and running on the target host, and you know its port (for example, `65212`).
- The machine running the browser can reach the host over the LAN.
- Port `65211` is free on the host (Piccolo's web port).
- For Option 1: [uv](https://docs.astral.sh/uv/) and Python 3.10+.
- For Option 2: Docker with Compose v2.

The examples below use `192.168.1.100` as the host IP and `65212` as the TigerVNC port. Replace them with your own values. Note that TigerVNC must accept connections from Piccolo: if it listens only on `127.0.0.1`, Piccolo must run on the same host, or the VNC server must be bound to a reachable network interface.

### Option 1: Run with uv

From the repository root:

```bash
uv run piccolo --ip 192.168.1.100 --port 65212
```

| Flag | Description |
| --- | --- |
| `--ip` | IP address of the host running TigerVNC |
| `--port` | Port of the TigerVNC server |

Piccolo starts its web service on port `65211`. Keep the process running.

### Option 2: Run with Docker Compose

Create a `docker-compose.yml` next to this README:

```yaml
services:
  piccolo:
    build: .
    image: piccolo:latest
    container_name: piccolo
    restart: unless-stopped
    ports:
      - "65211:65211"
    command:
      - "--ip"
      - "192.168.1.100"
      - "--port"
      - "65212"
```

Start it:

```bash
docker compose up -d
```

Confirm the container is running:

```bash
docker compose ps
```

> **Note** — If TigerVNC runs on the same machine as Docker, make sure the container can reach it. On Docker Desktop, `host.docker.internal` resolves to the host; on Linux you may need `network_mode: host` or an `extra_hosts` entry. If TigerVNC listens only on `127.0.0.1`, a bridge-networked container cannot reach it.

### Open the Desktop

In any browser on the LAN:

```
http://192.168.1.100:65211/vnc.html?autoconnect=true
```

- Replace `192.168.1.100` with the host's IP.
- `autoconnect=true` makes noVNC connect immediately when the page opens.
- Both installation methods expose the same URL.

If the page does not load, check that Piccolo is running, that port `65211` is open in the host firewall, and that Piccolo can reach the TigerVNC port.

## Use Cases

- **Agent-operated engineering software** — Let an Agent drive Ansys, ANSA, Cadence, or similar workstation applications on the machine where they are licensed and installed.
- **Human-in-the-loop automation** — The Agent works in the same desktop a person can watch, intervene in, or take over at any time.
- **Browser access to a workstation** — Reach a powerful office or lab machine from a laptop or tablet without installing a VNC client.
- **LAN lab and office machines** — Publish existing desktops to the local network with a single lightweight service.
- **Agent infrastructure for small teams** — Give agents a real execution machine without standing up a heavy sandbox platform.

## Security Notes

Piccolo is designed for **trusted local networks**.

- A VNC session grants **full control of the host desktop**. Treat the URL as a privileged credential.
- Set a VNC password on the TigerVNC server.
- Do **not** expose port `65211` directly to the public internet. Use a VPN, or a reverse proxy with TLS and authentication.
- Restrict access with firewall rules to the LAN or VPN ranges that need it.
- Traffic between Piccolo and TigerVNC is only as secure as the VNC configuration itself.

## Goals

The world already has many excellent Agent frameworks. What Agents still need is more **lightweight, convenient agent infrastructure and AI infrastructure** — so that individuals and small businesses can embrace AI at a lower cost.

Piccolo is built around that idea:

- **Lightweight by default** — one small service, not a platform.
- **Reuse what you already own** — real PCs, servers, and desktop sessions.
- **One command to start** — `uv run piccolo ...` or `docker compose up -d`.
- **Browser-first** — nothing to install on the device that views or drives the desktop.
- **Complementary, not competitive** — Piccolo works alongside sandbox middleware rather than replacing it.

## Documentation

- [简体中文 README](docs/README_zh.md)

## License

[MIT](LICENSE)
