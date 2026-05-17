from pydantic import BaseModel
from typing import Optional


class TelemetryDto(BaseModel):
    """Specchio esatto di TelemetryDto.kt nell'app Android."""
    registered: bool
    connected: bool
    productType: str
    isFlying: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    yaw: Optional[float] = None
    velocityX: Optional[float] = None
    velocityY: Optional[float] = None
    velocityZ: Optional[float] = None
    gpsSatellites: Optional[int] = None
    gpsSignal: Optional[str] = None
    flightMode: Optional[str] = None
    batteryPercent: Optional[int] = None


class SimpleResult(BaseModel):
    success: bool
    message: str


class StopMissionRequest(BaseModel):
    filename: str = ""


class StartMissionRequest(BaseModel):
    filename: str


class ModeRequest(BaseModel):
    mode: str  # "proxy" | "simulator"


class DjiSimulatorStartRequest(BaseModel):
    lat: float = 41.9028
    lon: float = 12.4964
    satellites: int = 12


class LatLon(BaseModel):
    lat: float
    lon: float


class MissionGenerateRequest(BaseModel):
    name: str
    altitude: float
    perimeter: list[LatLon]
    offsetMeters: float = 5.0
    speed: float = 8.0
    finishAction: str = "goHome"
    takeOffHeight: float = 20.0
    droneEnumValue: int = 77
    photoAtWaypoints: bool = False
    gimbalPitchDeg: float = -30.0


class SimPositionRequest(BaseModel):
    lat: float
    lon: float
