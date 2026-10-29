"""WebSocket-to-TCP proxy for the noVNC client."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import socket

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

BUFFER_SIZE = 64 * 1024
CONNECT_TIMEOUT = 10.0


async def proxy_websocket(websocket: WebSocket, vnc_host: str, vnc_port: int) -> None:
    """Bridge a noVNC WebSocket to a TigerVNC RFB TCP connection.

    noVNC sends the RFB protocol as binary WebSocket frames. This function
    accepts the browser connection, opens a TCP connection to TigerVNC, and
    pumps bytes in both directions until either side closes.
    """
    subprotocols = websocket.scope.get("subprotocols") or []
    subprotocol = "binary" if "binary" in subprotocols else None
    try:
        await websocket.accept(subprotocol=subprotocol)
    except Exception:
        return

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(vnc_host, vnc_port),
            timeout=CONNECT_TIMEOUT,
        )
    except (OSError, asyncio.TimeoutError) as exc:
        logger.warning("cannot connect to VNC server %s:%s: %s", vnc_host, vnc_port, exc)
        with contextlib.suppress(Exception):
            await websocket.close(code=1011, reason="Cannot connect to VNC server")
        return

    _enable_tcp_nodelay(writer)
    logger.debug("connected to VNC server %s:%s", vnc_host, vnc_port)

    tasks = [
        asyncio.create_task(_pump_vnc_to_client(reader, websocket), name="piccolo-vnc-to-client"),
        asyncio.create_task(_pump_client_to_vnc(websocket, writer), name="piccolo-client-to-vnc"),
    ]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                task.result()
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        with contextlib.suppress(Exception):
            await websocket.close()
        logger.debug("VNC proxy closed")


def _enable_tcp_nodelay(writer: asyncio.StreamWriter) -> None:
    sock = writer.get_extra_info("socket")
    if sock is None:
        return
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


async def _pump_vnc_to_client(reader: asyncio.StreamReader, websocket: WebSocket) -> None:
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                return
            await websocket.send_bytes(data)
    except (WebSocketDisconnect, RuntimeError, OSError):
        return


async def _pump_client_to_vnc(websocket: WebSocket, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            data = message.get("bytes")
            if data is None:
                text = message.get("text")
                if text is None:
                    continue
                data = text.encode()
            writer.write(data)
            await writer.drain()
    except (WebSocketDisconnect, RuntimeError, OSError):
        return
