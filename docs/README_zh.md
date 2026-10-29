# Piccolo

**将任意 Windows、Linux 或 macOS 个人 PC、服务器变成局域网内可通过浏览器访问的云端电脑 —— 并为 AI Agent 提供一台真正可操作的执行电脑。**

[English](../README.md) · [简体中文](README_zh.md)

Piccolo 是一个轻量级微服务：它基于 [noVNC](https://github.com/novnc/noVNC)，把宿主机上已有的 [TigerVNC](https://tigervnc.org/) 桌面发布到网页。没有额外的 Agent 运行时，没有容器沙箱，也没有重型编排 —— 只有你的机器、你的桌面，以及一个 URL。

## 目录

- [Piccolo 是什么？](#piccolo-是什么)
- [为什么还需要 Piccolo？](#为什么还需要-piccolo)
- [工作原理](#工作原理)
- [快速开始](#快速开始)
  - [前提条件](#前提条件)
  - [方式一：使用 uv 直接运行](#方式一使用-uv-直接运行)
  - [方式二：使用 Docker Compose 运行](#方式二使用-docker-compose-运行)
  - [打开桌面](#打开桌面)
- [典型使用场景](#典型使用场景)
- [安全说明](#安全说明)
- [我们的目标](#我们的目标)
- [文档](#文档)
- [许可证](#许可证)

## Piccolo 是什么？

Piccolo 可以将 Windows、Linux、macOS 的个人 PC、服务器，通过 VNC 变成**局域网内可通过网页访问的云端电脑**。任何带有浏览器的设备都能查看并控制这台机器的桌面。

在实际使用中，Piccolo 补齐的正是 AI Agent 与其需要操作的桌面软件之间的那一环：

- 宿主机继续运行 TigerVNC 和原有的桌面会话。
- Piccolo 提供 noVNC 客户端，并把浏览器的 WebSocket 连接桥接到 VNC 服务。
- 桌面通过一个局域网 URL 即可访问：`http://<宿主机IP>:65211/vnc.html?autoconnect=true`。
- Agent（或人）可以打开软件、点击、输入，完成真实的工作 —— 查看端不需要安装任何客户端。

### 一览

| 项目 | 说明 |
| --- | --- |
| 输入 | Windows / Linux / macOS 宿主机上已有的 TigerVNC 服务 |
| 输出 | 局域网内可通过浏览器访问的 noVNC 桌面 |
| 默认 Web 端口 | `65211` |
| 部署方式 | `uv run` 或 Docker Compose |
| 客户端要求 | 任意现代浏览器 |

## 为什么还需要 Piccolo？

Agent 生态里已经有很多沙箱中间件，E2B、OpenSandbox 等项目在各自领域也很优秀。但它们面向通用场景，对这个场景而言过于重型 —— 更重要的是，它们解决的是另一个问题。

Agent 需要操作的软件，往往**根本无法塞进小沙箱**：

- **Ansys、ANSA、Cadence** 等 CAD、CAE、EDA 软件工具，需要工作站级的 CPU、大容量内存、GPU，以及经过授权的完整桌面安装。
- 这些软件依赖完整的桌面环境，而不是一个精简的容器。
- 运行它们的硬件，通常就是个人工作站或服务器 —— 这些机器本来就已经存在。

Piccolo 走的是相反的路：不把工作负载搬进沙箱，而是**把浏览器带到已经装好软件的机器上**。

| | 容器沙箱（E2B、OpenSandbox 等） | Piccolo |
| --- | --- | --- |
| 执行单元 | 容器 | 已有的个人 PC 或服务器 |
| 最适合 | 不可信代码、短生命周期任务 | 重型桌面软件：CAD、CAE、EDA…… |
| 资源上限 | 受容器限制 | 整台机器 |
| 部署成本 | 构建镜像、编排沙箱 | 安装 TigerVNC，启动 Piccolo |
| 访问方式 | SDK / API | 任意浏览器，基于 noVNC |

Piccolo 并不是要取代沙箱，而是与沙箱互补：需要隔离代码执行时使用沙箱；需要真实桌面和真实软件时使用 Piccolo。

## 工作原理

```
┌─────────────────────────┐     HTTP + WebSocket      ┌─────────────────────────┐
│  浏览器 / Agent UI      │ ────────────────────────▶ │  Piccolo                │
│  noVNC 客户端           │ ◀──────────────────────── │  :65211                 │
└─────────────────────────┘                           └────────────┬────────────┘
                                                                   │ RFB over TCP
                                                                   ▼
                                                      ┌─────────────────────────┐
                                                      │  TigerVNC               │
                                                      │  :65212（示例）         │
                                                      └────────────┬────────────┘
                                                                   ▼
                                                      ┌─────────────────────────┐
                                                      │  宿主机桌面会话         │
                                                      │  Windows / Linux / macOS│
                                                      └─────────────────────────┘
```

1. 浏览器从 Piccolo 加载 noVNC Web 客户端。
2. noVNC 与 Piccolo 建立 WebSocket 连接。
3. Piccolo 通过 RFB 协议把会话转发给 TigerVNC 服务。
4. TigerVNC 呈现宿主机的真实桌面。

## 快速开始

### 前提条件

- 目标宿主机上已安装并运行 **TigerVNC**，且已知其端口（例如 `65212`）。
- 运行浏览器的设备能够通过局域网访问该宿主机。
- 宿主机上的 `65211` 端口未被占用（Piccolo 的 Web 端口）。
- 方式一：[uv](https://docs.astral.sh/uv/) 与 Python 3.10+。
- 方式二：Docker 与 Compose v2。

下文示例中，宿主机 IP 为 `192.168.1.100`，TigerVNC 端口为 `65212`，请替换为你自己的值。另外，TigerVNC 必须允许 Piccolo 连接：如果它只监听 `127.0.0.1`，Piccolo 就需要运行在同一台宿主机上，或者将 VNC 服务绑定到可访问的网络接口。

### 方式一：使用 uv 直接运行

在仓库根目录执行：

```bash
uv run piccolo --ip 192.168.1.100 --port 65212
```

| 参数 | 说明 |
| --- | --- |
| `--ip` | 运行 TigerVNC 的宿主机 IP |
| `--port` | TigerVNC 的端口 |

Piccolo 会在 `65211` 端口启动 Web 服务。保持进程运行即可。

### 方式二：使用 Docker Compose 运行

在 README 同级目录创建 `docker-compose.yml`：

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

启动：

```bash
docker compose up -d
```

确认容器成功运行：

```bash
docker compose ps
```

> **注意** —— 如果 TigerVNC 与 Docker 运行在同一台机器上，请确保容器能够访问它。在 Docker Desktop 上，`host.docker.internal` 指向宿主机；在 Linux 上可能需要 `network_mode: host` 或 `extra_hosts` 配置。如果 TigerVNC 只监听 `127.0.0.1`，使用桥接网络的容器将无法连接。

### 打开桌面

在局域网内任意浏览器中打开：

```
http://192.168.1.100:65211/vnc.html?autoconnect=true
```

- 将 `192.168.1.100` 替换为宿主机 IP。
- `autoconnect=true` 表示页面打开后自动连接 noVNC。
- 两种安装方式使用同一个访问地址。

如果页面无法打开，请检查 Piccolo 是否正在运行、宿主机防火墙是否放行 `65211` 端口，以及 Piccolo 是否能够连接到 TigerVNC 端口。

## 典型使用场景

- **Agent 操作工程软件** —— 让 Agent 在已授权、已安装软件的机器上驱动 Ansys、ANSA、Cadence 等工作站级应用。
- **人在回路（Human-in-the-loop）自动化** —— Agent 工作在人也能看到、能介入、能随时接管的同一桌面中。
- **通过浏览器访问工作站** —— 从笔记本或平板访问办公室、实验室的高性能机器，无需安装 VNC 客户端。
- **局域网实验室 / 办公机器** —— 用一个轻量服务，把已有桌面发布到内网。
- **小团队的 Agent 基础设施** —— 无需搭建重型沙箱平台，也能给 Agent 一台真实的执行电脑。

## 安全说明

Piccolo 面向**可信的局域网**设计。

- VNC 会话意味着对宿主机桌面的**完全控制权**。请把这个 URL 当作高权限凭证对待。
- 为 TigerVNC 设置 VNC 密码。
- **不要**把 `65211` 端口直接暴露到公网。请使用 VPN，或带 TLS 与身份认证的反向代理。
- 通过防火墙将访问限制在需要使用的局域网或 VPN 网段。
- Piccolo 与 TigerVNC 之间的流量安全性，取决于 VNC 本身的配置。

## 我们的目标

这个世界上已经有了很多优秀的 Agent 框架，但 Agent 需要更多**轻量级、便捷的 Agent 基础设施、AI 基础设施**，便于个人、小规模企业，用更小的代价拥抱 AI。

Piccolo 围绕这一目标构建：

- **默认轻量** —— 一个小服务，而不是一个平台。
- **复用已有资源** —— 真实的个人 PC、服务器和桌面会话。
- **一条命令启动** —— `uv run piccolo ...` 或 `docker compose up -d`。
- **浏览器优先** —— 查看或操作桌面的设备无需安装任何软件。
- **互补而非竞争** —— Piccolo 与沙箱中间件协同工作，而不是取代它们。

## 文档

- [English README](../README.md)

## 许可证

[MIT](../LICENSE)
