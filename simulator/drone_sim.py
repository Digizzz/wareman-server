import asyncio
import math
import time

from models import TelemetryDto
from simulator.waypoints import get_state, VERTICAL_SPEED_MS
from simulator.sim_state import update_simulated_telemetry
from ws_manager import manager

TICK_DT = 0.5  # secondi per tick (uguale all'intervallo WS di Android)
BATTERY_DRAIN_INTERVAL = 60.0  # secondi per perdere 1%


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distanza in metri tra due punti (lat, lon)."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _dist3d(wp_from: tuple, wp_to: tuple) -> float:
    horiz = _haversine(wp_from[0], wp_from[1], wp_to[0], wp_to[1])
    vert = abs(wp_to[2] - wp_from[2])
    return math.sqrt(horiz ** 2 + vert ** 2)


async def simulator_broadcast_task():
    """Task principale del simulatore: aggiorna lo stato e fa broadcast ogni TICK_DT secondi."""
    seg_idx = 0
    seg_progress = 0.0
    battery = 95
    last_drain = time.monotonic()
    current_version = -1   # rileva cambi di waypoint

    while True:
        await asyncio.sleep(TICK_DT)

        # Leggi lo stato corrente (waypoint + velocità + versione)
        waypoints, cruise_speed, version = get_state()

        # Se i waypoint sono cambiati, ricomincia dall'inizio
        if version != current_version:
            current_version = version
            seg_idx = 0
            seg_progress = 0.0
            battery = 95

        # Fine percorso → riparti dall'inizio
        if seg_idx >= len(waypoints) - 1:
            seg_idx = 0
            seg_progress = 0.0
            battery = 95

        wp_from = waypoints[seg_idx]
        wp_to   = waypoints[seg_idx + 1]

        # Velocità appropriata per il segmento
        only_vertical = (wp_from[0] == wp_to[0] and wp_from[1] == wp_to[1])
        speed = VERTICAL_SPEED_MS if only_vertical else cruise_speed

        seg_len = _dist3d(wp_from, wp_to)
        seg_progress += speed * TICK_DT

        # Avanza al segmento successivo se necessario
        if seg_progress >= seg_len or seg_len < 0.001:
            seg_idx += 1
            seg_progress = 0.0
            if seg_idx >= len(waypoints) - 1:
                continue
            wp_from = waypoints[seg_idx]
            wp_to   = waypoints[seg_idx + 1]
            seg_len = _dist3d(wp_from, wp_to)
            only_vertical = (wp_from[0] == wp_to[0] and wp_from[1] == wp_to[1])
            speed = VERTICAL_SPEED_MS if only_vertical else cruise_speed

        # Fattore di interpolazione t ∈ [0, 1]
        t = min(seg_progress / seg_len, 1.0) if seg_len > 0.001 else 1.0

        lat = wp_from[0] + (wp_to[0] - wp_from[0]) * t
        lon = wp_from[1] + (wp_to[1] - wp_from[1]) * t
        alt = wp_from[2] + (wp_to[2] - wp_from[2]) * t

        # Velocità e yaw
        horiz_dist = _haversine(wp_from[0], wp_from[1], wp_to[0], wp_to[1])
        vert_diff  = wp_to[2] - wp_from[2]
        total_3d   = _dist3d(wp_from, wp_to)

        if total_3d > 0.001:
            bearing = math.atan2(
                math.radians(wp_to[1] - wp_from[1]) * math.cos(math.radians(lat)),
                math.radians(wp_to[0] - wp_from[0]),
            )
            horiz_speed = speed * (horiz_dist / total_3d)
            vx = horiz_speed * math.cos(bearing)
            vy = horiz_speed * math.sin(bearing)
            vz = speed * (vert_diff / total_3d)
            yaw_deg = math.degrees(bearing) % 360
        else:
            vx = vy = vz = 0.0
            yaw_deg = 0.0

        # Batteria
        now = time.monotonic()
        if now - last_drain >= BATTERY_DRAIN_INTERVAL:
            battery = max(0, battery - 1)
            last_drain = now

        is_flying = alt > 0.5
        flight_mode = "WAYPOINT_MISSION" if is_flying else "ON_GROUND"

        telemetry = TelemetryDto(
            registered=True,
            connected=True,
            productType="Matrice 350 RTK (Sim)",
            isFlying=is_flying,
            latitude=round(lat, 7),
            longitude=round(lon, 7),
            altitude=round(alt, 2),
            pitch=round(-5.0 if (horiz_dist > 0 and vz == 0) else 0.0, 2),
            roll=0.0,
            yaw=round(yaw_deg, 2),
            velocityX=round(vx, 3),
            velocityY=round(vy, 3),
            velocityZ=round(vz, 3),
            gpsSatellites=14,
            gpsSignal="LEVEL_5",
            flightMode=flight_mode,
            batteryPercent=battery,
        )

        update_simulated_telemetry(telemetry)
        await manager.broadcast(telemetry.model_dump_json())
