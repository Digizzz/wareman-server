import threading

# Percorso di volo di default: survey rettangolare (Roma)
# Ogni tupla: (latitudine, longitudine, altitudine_m)
DEFAULT_WAYPOINTS: list[tuple[float, float, float]] = [
    (41.9028, 12.4964,  0.0),   # home / punto di decollo
    (41.9028, 12.4964, 30.0),   # salita a 30 m
    (41.9038, 12.4964, 30.0),   # tratto nord
    (41.9038, 12.4984, 30.0),   # tratto est
    (41.9028, 12.4984, 30.0),   # tratto sud
    (41.9028, 12.4964, 30.0),   # tratto ovest (ritorno colonna)
    (41.9028, 12.4964,  5.0),   # discesa a 5 m
    (41.9028, 12.4964,  0.0),   # atterraggio
]

CRUISE_SPEED_MS   = 8.0   # m/s in orizzontale
VERTICAL_SPEED_MS = 2.0   # m/s in salita/discesa

# ── Stato mutabile thread-safe ───────────────────────────────────────────────
_lock = threading.Lock()
_waypoints: list[tuple[float, float, float]] = list(DEFAULT_WAYPOINTS)
_cruise_speed: float = CRUISE_SPEED_MS
_version: int = 0   # incrementato ad ogni cambio; drone_sim lo usa per ripartire


def get_state() -> tuple[list[tuple[float, float, float]], float, int]:
    """Restituisce (waypoints, cruise_speed, version) in modo thread-safe."""
    with _lock:
        return list(_waypoints), _cruise_speed, _version


def set_waypoints(wps: list[tuple[float, float, float]], speed: float = CRUISE_SPEED_MS) -> None:
    """Sostituisce i waypoint correnti e forza il riavvio del simulatore."""
    global _waypoints, _cruise_speed, _version
    with _lock:
        _waypoints = list(wps)
        _cruise_speed = speed
        _version += 1


def set_home_position(lat: float, lon: float) -> None:
    """Trasla tutti i waypoint correnti affinché l'home coincida con (lat, lon)."""
    global _waypoints, _version
    with _lock:
        if not _waypoints:
            return
        dlat = lat - _waypoints[0][0]
        dlon = lon - _waypoints[0][1]
        _waypoints = [(wp[0] + dlat, wp[1] + dlon, wp[2]) for wp in _waypoints]
        _version += 1


def build_mission_waypoints(
    home_lat: float,
    home_lon: float,
    perimeter: list[tuple[float, float]],
    altitude: float,
    speed: float,
    takeoff_height: float = 20.0,
) -> list[tuple[float, float, float]]:
    """
    Costruisce la sequenza completa di waypoint da un perimetro GPS.

    Sequenza: home → salita sicurezza → vertici perimetro (loop chiuso)
              → ritorno home ad altitudine → discesa → atterraggio
    """
    wps: list[tuple[float, float, float]] = [
        (home_lat, home_lon, 0.0),            # decollo
        (home_lat, home_lon, takeoff_height), # salita
    ]
    for lat, lon in perimeter:
        wps.append((lat, lon, altitude))

    # Chiudi il loop se l'ultimo vertice != primo
    if len(perimeter) >= 2:
        if perimeter[-1] != perimeter[0]:
            wps.append((perimeter[0][0], perimeter[0][1], altitude))

    # Rientro home e atterraggio
    wps.append((home_lat, home_lon, altitude))
    wps.append((home_lat, home_lon, 5.0))
    wps.append((home_lat, home_lon, 0.0))
    return wps
