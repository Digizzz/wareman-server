# wareman-server

FastAPI server that sits between the [WareMan Android app](https://github.com/Digizzz/WareMan) and the [dashboard](https://github.com/Digizzz/wareman-dashboard). Runs on a PC or any machine on the same Wi-Fi network as the DJI RC.

Two operating modes:

- **proxy** — forwards all requests to the Android app on the RC and relays WebSocket telemetry in real time
- **simulator** — runs a virtual drone locally, no hardware required

## Requirements

- Python 3.11+
- `go2rtc` binary placed in `go2rtc/` (for RTSP video relay)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

Server starts on `http://0.0.0.0:9000`. The dashboard is served at `/` and `/dashboard`.

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANDROID_IP` | `192.168.43.1` | IP of the DJI RC (hotspot gateway) |
| `ANDROID_PORT` | `8080` | WareMan API port on the RC |
| `SERVER_PORT` | `9000` | Port this server listens on |
| `WAREMAN_MODE` | `proxy` | `proxy` or `simulator` |
| `GO2RTC_BINARY` | `./go2rtc/go2rtc.exe` | Path to go2rtc binary |
| `GO2RTC_API_PORT` | `1984` | go2rtc management API port |
| `GO2RTC_RTSP_PORT` | `8555` | go2rtc RTSP output port |

Mode can also be switched at runtime via the `/config/mode` endpoint without restarting.

## API

The server exposes the same REST/WebSocket API as WareMan (proxied or simulated), plus:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/config` | Current config (mode, Android IP) |
| POST | `/config/mode` | Switch mode at runtime |
| POST | `/config/android-ip` | Update Android IP at runtime |

Full interactive docs available at `http://localhost:9000/docs`.

## Architecture

```
main.py
  ├── proxy/ws_relay.py      – WebSocket relay from Android to dashboard clients
  ├── simulator/drone_sim.py – virtual drone that broadcasts fake telemetry
  ├── video/go2rtc_manager.py– manages go2rtc process for RTSP relay
  ├── routers/               – FastAPI routers (telemetry, mission, rtsp, simulator, config)
  └── static/                – built dashboard frontend
```

## Related repos

- [WareMan](https://github.com/Digizzz/WareMan) — Android app running on the DJI RC
- [wareman-dashboard](https://github.com/Digizzz/wareman-dashboard) — React control dashboard
