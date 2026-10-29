# Piccolo

**将任意 Windows、Linux 或 macOS 个人 PC、服务器变成局域网内可通过浏览器访问的云端电脑 —— 并为 AI Agent 提供一台真正可操作的执行电脑。**

[English](../README.md) · [简体中文](README_zh.md)

Piccolo 是一个轻量级微服务：它基于 [noVNC](https://github.com/novnc/noVNC)，把宿主机上已有的 [TigerVNC](https://tigervnc.org/) 桌面发布到网页。没有额外的 Agent 运行时，没有容器沙箱，也没有重型编排 —— 只有你的机器、你的桌面，以及一个 URL。

## 目录

- [Piccolo 是什么？](#piccolo-是什么)
- [名字的由来](#名字的由来)
- [为什么还需要 Piccolo？](#为什么还需要-piccolo)
- [工作原理](#工作原理)
- [快速开始](#快速开始)
  - [前提条件](#前提条件)
  - [方式一：使用 uv 直接运行](#方式一使用-uv-直接运行)
  - [方式二：使用 Docker Compose 运行](#方式二使用-docker-compose-运行)
  - [打开桌面](#打开桌面)
- [配置](#配置)
- [典型使用场景](#典型使用场景)
- [安全说明](#安全说明)
- [开发](#开发)
- [我们的目标](#我们的目标)
- [第三方组件](#第三方组件)
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
| 运行环境 | Python 3.10+（FastAPI + uvicorn） |
| 部署方式 | `uv run` 或 Docker Compose |
| 客户端要求 | 任意现代浏览器 |

## 名字的由来

Piccolo 的名字取自《七龙珠》中的**比克大魔王**。初代比克大魔王最怕**魔封波** —— 正是通过魔封波，他被封印进了电饭锅中。我们希望 Piccolo 就像那个与魔封波相关的电饭锅一样，为 Agent 提供一个**便捷、安全可靠的环境**。

![封印比克大魔王的魔封波电饭锅](piccolo.png)

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
                                                      │  :65201（示例）         │
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

- 目标宿主机上已安装并运行 **TigerVNC**，且已知其端口（例如 `65201`）。
- 运行浏览器的设备能够通过局域网访问该宿主机。
- 宿主机上的 `65211` 端口未被占用（Piccolo 的 Web 端口）。
- 方式一：[uv](https://docs.astral.sh/uv/) 与 Python 3.10+。
- 方式二：Docker 与 Compose v2。

下文示例中，宿主机 IP 为 `192.168.31.102`，TigerVNC 端口为 `65201`，请替换为你自己的值。另外，TigerVNC 必须允许 Piccolo 连接：如果它只监听 `127.0.0.1`，Piccolo 就需要运行在同一台宿主机上，或者将 VNC 服务绑定到可访问的网络接口。

### 方式一：使用 uv 直接运行

在仓库根目录执行：

```bash
uv run piccolo --ip 192.168.31.102 --port 65201
```

| 参数 | 说明 |
| --- | --- |
| `--ip` | 运行 TigerVNC 的宿主机 IP |
| `--port` | TigerVNC 的端口 |

Piccolo 会在 `65211` 端口启动 Web 服务。保持进程运行即可。

### 方式二：使用 Docker Compose 运行

仓库已提供 `docker-compose.yml`，它会构建 Piccolo、映射 `65211` 端口，并从环境变量读取 VNC 目标：

```bash
cp .env.example .env
# 如果 TigerVNC 不在 Docker 宿主机上，或端口不同，请编辑 .env
docker compose up -d
docker compose ps
```

默认情况下，compose 文件指向 `host.docker.internal:65201` —— 即容器视角下的 Docker 宿主机。如果 TigerVNC 运行在另一台局域网机器上，请把 `PICCOLO_VNC_HOST` 设置为那台机器的 IP 或主机名。`extra_hosts` 配置让 `host.docker.internal` 在 Linux 上也可用。如果构建时默认 PyPI 源较慢，可以在 `.env` 中设置 `PIP_INDEX_URL`（参考 `.env.example`）。

> **注意** —— 如果 TigerVNC 只监听 `127.0.0.1`，使用桥接网络的容器将无法连接。请将 TigerVNC 绑定到可访问的网络接口，或直接在宿主机上用 `uv run` 运行 Piccolo。

### 打开桌面

在局域网内任意浏览器中打开：

```
http://192.168.31.102:65211/vnc.html?autoconnect=true
```

- 将 `192.168.31.102` 替换为宿主机 IP。
- `autoconnect=true` 表示页面打开后自动连接 noVNC。
- 两种安装方式使用同一个访问地址。

如果页面无法打开，请检查 Piccolo 是否正在运行、宿主机防火墙是否放行 `65211` 端口，以及 Piccolo 是否能够连接到 TigerVNC 端口。

## 配置

所有参数都可以通过命令行参数或环境变量提供，命令行参数优先。

| 命令行参数 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--ip` | `PICCOLO_VNC_HOST` | 必填 | TigerVNC 服务器的 IP 或主机名 |
| `--port` | `PICCOLO_VNC_PORT` | 必填 | TigerVNC 端口（例如 `65201`） |
| `--web-host` | `PICCOLO_WEB_HOST` | `0.0.0.0` | Piccolo Web 服务绑定地址 |
| `--web-port` | `PICCOLO_WEB_PORT` | `65211` | noVNC 与 WebSocket 端口 |
| `--log-level` | `PICCOLO_LOG_LEVEL` | `info` | `critical`、`error`、`warning`、`info`、`debug` 或 `trace` |

示例：

```bash
# 显式参数
uv run piccolo --ip 192.168.31.102 --port 65201 --web-port 65211

# 或使用环境变量
PICCOLO_VNC_HOST=192.168.31.102 PICCOLO_VNC_PORT=65201 uv run piccolo
```

根路径 `/` 会重定向到 `/vnc.html?autoconnect=true`。健康检查接口为 `/health`：

```bash
curl http://192.168.31.102:65211/health
# {"status":"ok","service":"piccolo","version":"0.1.0"}
```

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

## 开发

```bash
uv sync              # 创建虚拟环境并安装依赖
uv run pytest        # 运行测试
uv run ruff check .  # 代码检查
uv build             # 构建 sdist + wheel 到 dist/
```

项目结构：

| 路径 | 作用 |
| --- | --- |
| `src/piccolo/app.py` | FastAPI 应用、健康检查、noVNC 静态服务 |
| `src/piccolo/proxy.py` | WebSocket ↔ TigerVNC TCP 双向转发 |
| `src/piccolo/cli.py` | `piccolo` 命令行与环境变量处理 |
| `src/piccolo/web/vncs/` | 内置的 noVNC 1.7.0 资源 |

构建容器：

```bash
docker build -t piccolo:latest .
```

如果默认 PyPI 源较慢，可以在构建时指定镜像源：

```bash
docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t piccolo:latest .
```

## 我们的目标

这个世界上已经有了很多优秀的 Agent 框架，但 Agent 需要更多**轻量级、便捷的 Agent 基础设施、AI 基础设施**，便于个人、小规模企业，用更小的代价拥抱 AI。

Piccolo 围绕这一目标构建：

- **默认轻量** —— 一个小服务，而不是一个平台。
- **复用已有资源** —— 真实的个人 PC、服务器和桌面会话。
- **一条命令启动** —— `uv run piccolo ...` 或 `docker compose up -d`。
- **浏览器优先** —— 查看或操作桌面的设备无需安装任何软件。
- **互补而非竞争** —— Piccolo 与沙箱中间件协同工作，而不是取代它们。

## 第三方组件

`src/piccolo/web/vncs/` 下内置的 noVNC 客户端为 **noVNC 1.7.0**，采用 Mozilla Public License 2.0（MPL 2.0）许可。完整许可以及内置组件各自的许可证见 `src/piccolo/web/vncs/LICENSE.txt`。Piccolo 自身代码采用 MIT 许可。

## 文档

- [English README](../README.md)

## 许可证

[MIT](../LICENSE)
