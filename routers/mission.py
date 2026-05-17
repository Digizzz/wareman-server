from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import httpx
import config
from proxy.http_proxy import proxy_get, proxy_post, proxy_post_file
from models import SimpleResult, StopMissionRequest, StartMissionRequest, MissionGenerateRequest

router = APIRouter(prefix="/mission", tags=["mission"])


def _proxy_error(e: Exception) -> JSONResponse:
    if isinstance(e, httpx.HTTPStatusError):
        try:
            body = e.response.json()
        except Exception:
            body = {"message": e.response.text or str(e)}
        msg = body.get("message") or body.get("error") or str(e)
        return JSONResponse(status_code=502, content={"success": False, "message": msg, **body})
    return JSONResponse(status_code=502, content={"success": False, "message": str(e)})


@router.post("/pause", response_model=SimpleResult)
async def pause():
    if config.MODE == "simulator":
        return SimpleResult(success=True, message="Simulator: missione in pausa")
    try:
        return await proxy_post("/mission/pause")
    except Exception as e:
        return _proxy_error(e)


@router.post("/resume", response_model=SimpleResult)
async def resume():
    if config.MODE == "simulator":
        return SimpleResult(success=True, message="Simulator: missione ripresa")
    try:
        return await proxy_post("/mission/resume")
    except Exception as e:
        return _proxy_error(e)


@router.post("/stop", response_model=SimpleResult)
async def stop(body: StopMissionRequest):
    if config.MODE == "simulator":
        name = body.filename or "corrente"
        return SimpleResult(success=True, message=f"Simulator: missione '{name}' fermata")
    try:
        return await proxy_post("/mission/stop", json={"filename": body.filename})
    except Exception as e:
        return _proxy_error(e)


@router.get("/status")
async def status():
    if config.MODE == "simulator":
        return {"currentMission": ""}
    try:
        return await proxy_get("/mission/status")
    except Exception as e:
        return _proxy_error(e)


@router.get("/folder")
async def folder():
    if config.MODE == "simulator":
        return {"path": "/simulator/missions"}
    try:
        return await proxy_get("/mission/folder")
    except Exception as e:
        return _proxy_error(e)


@router.post("/upload", response_model=SimpleResult)
async def upload(file: UploadFile = File(...)):
    if config.MODE == "simulator":
        return SimpleResult(success=True, message=f"Simulator: file '{file.filename}' ricevuto, missione avviata")
    try:
        data = await file.read()
        return await proxy_post_file("/mission/upload", file.filename or "mission.kmz", data)
    except Exception as e:
        return _proxy_error(e)


@router.post("/start", response_model=SimpleResult)
async def start(body: StartMissionRequest):
    if config.MODE == "simulator":
        return SimpleResult(success=True, message=f"Simulator: missione '{body.filename}' avviata")
    try:
        return await proxy_post("/mission/start", json={"filename": body.filename})
    except Exception as e:
        return _proxy_error(e)


@router.post("/generate", response_model=SimpleResult)
async def generate(body: MissionGenerateRequest):
    if config.MODE == "simulator":
        from simulator.sim_state import get_simulated_telemetry
        from simulator.waypoints import build_mission_waypoints, set_waypoints
        tel = get_simulated_telemetry()
        home_lat = tel.latitude if tel.latitude is not None else body.perimeter[0].lat
        home_lon = tel.longitude if tel.longitude is not None else body.perimeter[0].lon
        perimeter = [(p.lat, p.lon) for p in body.perimeter]
        wps = build_mission_waypoints(
            home_lat, home_lon, perimeter,
            body.altitude, body.speed, body.takeOffHeight,
        )
        set_waypoints(wps, body.speed)
        return SimpleResult(
            success=True,
            message=(
                f"Simulatore: missione '{body.name}' avviata "
                f"({len(perimeter)} vertici, {body.altitude}m, {body.speed}m/s)"
            ),
        )
    try:
        # 1. Genera il KMZ sull'RC
        raw = await proxy_post("/mission/generate", json=body.model_dump())
        ok = str(raw.get("success", "false")).lower() == "true"
        if not ok:
            msg = raw.get("message") or raw.get("error") or "Errore generazione missione"
            return SimpleResult(success=False, message=msg)

        filename = raw.get("filename", body.name)
        wps = raw.get("waypointCount", "?")

        # 2. Avvia la missione (upload sul drone + start): timeout lungo perché
        #    pushKMZFileToAircraft può richiedere 20-30 s su hardware reale
        async with httpx.AsyncClient(
            base_url=f"http://{config.ANDROID_IP}:{config.ANDROID_PORT}",
            timeout=120.0,
        ) as client:
            r = await client.post("/mission/start", json={"filename": filename})
            r.raise_for_status()
            start_raw = r.json()

        start_ok = start_raw.get("success", True)
        if not start_ok:
            err = start_raw.get("message") or start_raw.get("error") or "Errore avvio"
            return SimpleResult(success=False, message=f"KMZ generato ma avvio fallito: {err}")

        return SimpleResult(success=True, message=f"Missione '{filename}' generata e avviata ({wps} waypoint)")
    except Exception as e:
        return _proxy_error(e)
