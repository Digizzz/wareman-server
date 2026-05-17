from fastapi import APIRouter
from fastapi.responses import JSONResponse
import config
from proxy.http_proxy import proxy_get
from simulator.sim_state import get_simulated_telemetry
from models import TelemetryDto

router = APIRouter(tags=["telemetry"])


@router.get("/health")
async def health():
    if config.MODE == "proxy":
        try:
            return await proxy_get("/health")
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})
    return {"status": "ok", "service": "WareMan simulator"}


@router.get("/telemetry", response_model=TelemetryDto)
async def telemetry():
    if config.MODE == "proxy":
        try:
            return await proxy_get("/telemetry")
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})
    return get_simulated_telemetry()


@router.get("/battery")
async def battery():
    if config.MODE == "proxy":
        try:
            return await proxy_get("/battery")
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})
    t = get_simulated_telemetry()
    return {"batteryPercent": t.batteryPercent}
