import asyncio
from fastapi import WebSocket
from typing import Set


class ConnectionManager:
    """Fan-out broadcaster: una sorgente (Android o simulatore) → N client React."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.active_connections.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self.active_connections.discard(ws)

    async def broadcast(self, message: str):
        async with self._lock:
            targets = set(self.active_connections)
        dead: Set[WebSocket] = set()
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self.active_connections -= dead


# Singleton condiviso da tutti i moduli
manager = ConnectionManager()
