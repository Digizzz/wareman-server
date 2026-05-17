from fastapi import APIRouter
from pydantic import BaseModel
import config

router = APIRouter(prefix="/config", tags=["config"])


class AndroidConfig(BaseModel):
    ip: str
    port: int = 8080


@router.get("/android")
async def get_android_config():
    return {"ip": config.ANDROID_IP, "port": config.ANDROID_PORT}


@router.post("/android")
async def set_android_config(body: AndroidConfig):
    """Aggiorna IP/porta Android a runtime e riavvia relay + go2rtc."""
    config.update_android_ip(body.ip, body.port)

    from main import switch_mode
    await switch_mode(config.MODE)

    return {"ip": config.ANDROID_IP, "port": config.ANDROID_PORT}
