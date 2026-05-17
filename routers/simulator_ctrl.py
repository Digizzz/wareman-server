from fastapi import APIRouter
from fastapi.responses import JSONResponse
import config
from models import ModeRequest, DjiSimulatorStartRequest, SimPositionRequest
from proxy.http_proxy import proxy_get, proxy_post

router = APIRouter(tags=["simulator"])


@router.get("/simulator/mode")
async def get_mode():
    return {"mode": config.MODE}


@router.post("/simulator/mode")
async def set_mode(body: ModeRequest):
    """Cambia modalità a runtime senza riavviare il server."""
    if body.mode not in ("proxy", "simulator"):
        return JSONResponse(status_code=400, content={"error": "mode deve essere 'proxy' o 'simulator'"})

    from main import switch_mode
    await switch_mode(body.mode)
    return {"mode": config.MODE}


@router.post("/dji-simulator/start")
async def dji_simulator_start(body: DjiSimulatorStartRequest):
    """Avvia il simulatore interno del DJI SDK sull'Android (richiede controller connesso)."""
    if config.MODE != "proxy":
        return JSONResponse(status_code=400, content={"error": "Disponibile solo in modalità proxy"})
    try:
        return await proxy_post("/dji-simulator/start", json=body.model_dump())
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})


@router.post("/dji-simulator/stop")
async def dji_simulator_stop():
    """Ferma il simulatore interno del DJI SDK sull'Android."""
    if config.MODE != "proxy":
        return JSONResponse(status_code=400, content={"error": "Disponibile solo in modalità proxy"})
    try:
        return await proxy_post("/dji-simulator/stop")
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})


@router.get("/dji-simulator/status")
async def dji_simulator_status():
    """Restituisce se il simulatore DJI è attivo sull'Android."""
    if config.MODE != "proxy":
        return {"enabled": False, "note": "modalità simulator Python attiva, non DJI"}
    try:
        return await proxy_get("/dji-simulator/status")
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})


@router.post("/simulator/position")
async def set_sim_position(body: SimPositionRequest):
    """Imposta la posizione home del simulatore Python (sposta i waypoint correnti)."""
    from simulator.waypoints import set_home_position
    set_home_position(body.lat, body.lon)
    return {
        "success": True,
        "message": f"Posizione simulatore impostata: {body.lat:.6f}, {body.lon:.6f}",
    }
