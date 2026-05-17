import threading
from models import TelemetryDto

_lock = threading.Lock()

_state = TelemetryDto(
    registered=True,
    connected=True,
    productType="Matrice 350 RTK (Sim)",
    isFlying=False,
    latitude=41.9028,
    longitude=12.4964,
    altitude=0.0,
    pitch=0.0,
    roll=0.0,
    yaw=0.0,
    velocityX=0.0,
    velocityY=0.0,
    velocityZ=0.0,
    gpsSatellites=14,
    gpsSignal="LEVEL_5",
    flightMode="ON_GROUND",
    batteryPercent=95,
)


def get_simulated_telemetry() -> TelemetryDto:
    with _lock:
        return _state.model_copy()


def update_simulated_telemetry(new: TelemetryDto) -> None:
    global _state
    with _lock:
        _state = new
