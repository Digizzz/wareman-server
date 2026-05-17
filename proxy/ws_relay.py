import asyncio
import websockets
import config
from ws_manager import manager


async def android_ws_relay_task():
    """Relay con riconnessione automatica: Android /ws/telemetry → tutti i client React."""
    while True:
        try:
            async with websockets.connect(config.ANDROID_WS_URL) as ws:
                async for message in ws:
                    await manager.broadcast(str(message))
        except asyncio.CancelledError:
            raise
        except Exception:
            # Android non raggiungibile o connessione persa — riprova tra 2s
            await asyncio.sleep(2.0)
