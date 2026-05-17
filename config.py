import os

# IP del dispositivo Android (gateway hotspot di default)
ANDROID_IP   = os.getenv("ANDROID_IP", "192.168.43.1")
ANDROID_PORT = int(os.getenv("ANDROID_PORT", "8080"))
ANDROID_BASE_URL = f"http://{ANDROID_IP}:{ANDROID_PORT}"
ANDROID_WS_URL   = f"ws://{ANDROID_IP}:{ANDROID_PORT}/ws/telemetry"


def update_android_ip(ip: str, port: int | None = None) -> None:
    """Aggiorna IP Android a runtime — i moduli leggono config.ANDROID_IP direttamente."""
    global ANDROID_IP, ANDROID_PORT, ANDROID_BASE_URL, ANDROID_WS_URL
    ANDROID_IP = ip
    if port is not None:
        ANDROID_PORT = port
    ANDROID_BASE_URL = f"http://{ANDROID_IP}:{ANDROID_PORT}"
    ANDROID_WS_URL   = f"ws://{ANDROID_IP}:{ANDROID_PORT}/ws/telemetry"

# Porta del server Python
SERVER_PORT = int(os.getenv("SERVER_PORT", "9000"))

# Modalità: "proxy" → forward verso Android, "simulator" → drone simulato
MODE = os.getenv("WAREMAN_MODE", "proxy")

# go2rtc
GO2RTC_BINARY    = os.getenv("GO2RTC_BINARY", "./go2rtc/go2rtc.exe")
GO2RTC_API_PORT  = int(os.getenv("GO2RTC_API_PORT", "1984"))
GO2RTC_RTSP_PORT = int(os.getenv("GO2RTC_RTSP_PORT", "8555"))

# URL RTSP del drone reale (esposto da Android)
RTSP_ANDROID_URL = f"rtsp://admin:admin123@{ANDROID_IP}:8554/streaming/live/1"
