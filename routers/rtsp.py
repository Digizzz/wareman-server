from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
import httpx
import config
from proxy.http_proxy import proxy_get, proxy_post

router = APIRouter(prefix="/rtsp", tags=["rtsp"])


def _android_error(e: Exception) -> JSONResponse:
    """Estrae il messaggio di errore da Android e lo restituisce al client."""
    if isinstance(e, httpx.HTTPStatusError):
        try:
            body = e.response.json()
        except Exception:
            body = {"error": e.response.text or str(e)}
        print(f"[rtsp] Errore Android {e.response.status_code}: {body}")
        return JSONResponse(status_code=502, content={"success": False, **body})
    print(f"[rtsp] Errore proxy: {e}")
    return JSONResponse(status_code=502, content={"success": False, "error": str(e)})


@router.post("/start")
async def rtsp_start():
    if config.MODE == "simulator":
        return {
            "success": True,
            "rtspUrl": f"rtsp://localhost:{config.GO2RTC_RTSP_PORT}/drone_live",
            "webrtc": f"http://localhost:{config.GO2RTC_API_PORT}",
        }
    try:
        return await proxy_post("/rtsp/start")
    except Exception as e:
        return _android_error(e)


@router.post("/stop")
async def rtsp_stop():
    if config.MODE == "simulator":
        return {"success": True, "message": "Simulator RTSP fermato"}
    try:
        return await proxy_post("/rtsp/stop")
    except Exception as e:
        return _android_error(e)


@router.get("/status")
async def rtsp_status():
    if config.MODE == "simulator":
        return {
            "streaming": True,
            "cameraIndex": "SIMULATOR",
            "availableCameras": "LEFT_OR_MAIN",
            "videoSource": "WIDE_CAMERA",
            "availableVideoSources": "WIDE_CAMERA,INFRARED_CAMERA",
        }
    try:
        return await proxy_get("/rtsp/status")
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})


@router.post("/camera")
async def rtsp_camera(body: dict):
    if config.MODE == "simulator":
        return {"success": True, "camera": body.get("index", "LEFT_OR_MAIN")}
    try:
        return await proxy_post("/rtsp/camera", json=body)
    except Exception as e:
        return _android_error(e)


@router.post("/source")
async def rtsp_source(body: dict = Body(default_factory=dict)):
    if config.MODE == "simulator":
        return {"success": True, "source": body.get("source", "WIDE_CAMERA")}
    try:
        return await proxy_post("/rtsp/source", json=body)
    except Exception as e:
        return _android_error(e)
