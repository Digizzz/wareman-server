import asyncio
import os as _os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import config
from ws_manager import manager
from routers import telemetry, mission, rtsp, simulator_ctrl, config_router
from video.go2rtc_manager import start_go2rtc, stop_go2rtc

# ─── Task di background (relay Android o simulatore) ────────────────────────

_bg_task: asyncio.Task | None = None


async def _start_bg_task(mode: str) -> None:
    global _bg_task
    if _bg_task and not _bg_task.done():
        _bg_task.cancel()
        try:
            await _bg_task
        except asyncio.CancelledError:
            pass

    if mode == "proxy":
        from proxy.ws_relay import android_ws_relay_task
        _bg_task = asyncio.create_task(android_ws_relay_task(), name="ws-relay")
        print(f"[wareman] Modalita PROXY -> Android {config.ANDROID_BASE_URL}")
    else:
        from simulator.drone_sim import simulator_broadcast_task
        _bg_task = asyncio.create_task(simulator_broadcast_task(), name="sim-drone")
        print("[wareman] Modalita SIMULATOR -> drone virtuale attivo")


async def switch_mode(new_mode: str) -> None:
    """Cambia modalità a runtime: aggiorna config, riavvia task e go2rtc."""
    config.MODE = new_mode
    await _start_bg_task(new_mode)
    await start_go2rtc(new_mode)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _start_bg_task(config.MODE)
    await start_go2rtc(config.MODE)
    yield
    if _bg_task and not _bg_task.done():
        _bg_task.cancel()
    await stop_go2rtc()


# ─── App FastAPI ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="WareMan Proxy/Simulator Server",
    description="Proxy verso Android e simulatore drone DJI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS aperto per i client React in sviluppo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(mission.router)
app.include_router(rtsp.router)
app.include_router(simulator_ctrl.router)
app.include_router(config_router.router)

# ─── Static files & dashboard ────────────────────────────────────────────────

_static_dir = _os.path.join(_os.path.dirname(__file__), "static")
if _os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse(_os.path.join(_static_dir, "index.html"))


# ─── WebSocket telemetria (fan-out a tutti i client React) ───────────────────

@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantiene la connessione viva; i dati arrivano tramite manager.broadcast()
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.SERVER_PORT,
        reload=False,
    )
