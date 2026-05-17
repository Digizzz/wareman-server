"""
Genera test_mission.kmz — quadrato 4 waypoint a Roma, altitudine 30m.
Formato: DJI WPML v1.0.0 (compatibile DJI SDK v5 + simulatore).
Esegui: python generate_test_mission.py
"""
import io
import time
import zipfile

# Coordinate centro (default simulatore DJI)
CENTER_LAT = 44.378160
CENTER_LON = 7.526832
ALT = 2       # metri (relativo al punto di decollo)
SPEED = 1.0    # m/s
OFFSET = 0.0008  # ~90 metri

# 4 waypoint: Nord → Est → Sud → Ovest
WAYPOINTS = [
    (CENTER_LAT + OFFSET, CENTER_LON,          ALT),  # N
    (CENTER_LAT,          CENTER_LON + OFFSET, ALT),  # E
    (CENTER_LAT - OFFSET, CENTER_LON,          ALT),  # S
    (CENTER_LAT,          CENTER_LON - OFFSET, ALT),  # W
]

NOW_MS = int(time.time() * 1000)


def placemark(index: int, lat: float, lon: float, alt: float) -> str:
    return f"""    <Placemark>
      <Point><coordinates>{lon},{lat},{alt}</coordinates></Point>
      <wpml:index>{index}</wpml:index>
      <wpml:executeHeight>{alt}</wpml:executeHeight>
      <wpml:waypointSpeed>{SPEED}</wpml:waypointSpeed>
      <wpml:waypointHeadingParam>
        <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
      </wpml:waypointHeadingParam>
      <wpml:waypointTurnParam>
        <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
        <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
      </wpml:waypointTurnParam>
      <wpml:useStraightLine>1</wpml:useStraightLine>
    </Placemark>"""


def wayline_point(index: int, lat: float, lon: float, alt: float) -> str:
    return f"""    <Placemark>
      <Point><coordinates>{lon},{lat},{alt}</coordinates></Point>
      <wpml:index>{index}</wpml:index>
      <wpml:waypointSpeed>{SPEED}</wpml:waypointSpeed>
      <wpml:executeHeight>{alt}</wpml:executeHeight>
      <wpml:waypointHeadingParam>
        <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
        <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
      </wpml:waypointHeadingParam>
      <wpml:waypointTurnParam>
        <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
        <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
      </wpml:waypointTurnParam>
      <wpml:useStraightLine>1</wpml:useStraightLine>
      <wpml:gimbalPitchAngle>0</wpml:gimbalPitchAngle>
      <wpml:actionGroup>
        <wpml:actionGroupId>{index}</wpml:actionGroupId>
        <wpml:actionGroupStartIndex>{index}</wpml:actionGroupStartIndex>
        <wpml:actionGroupEndIndex>{index}</wpml:actionGroupEndIndex>
        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
        <wpml:actionTrigger>
          <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
        </wpml:actionTrigger>
        <wpml:action>
          <wpml:actionId>0</wpml:actionId>
          <wpml:actionActuatorFunc>hover</wpml:actionActuatorFunc>
          <wpml:actionActuatorFuncParam>
            <wpml:hoverTime>1</wpml:hoverTime>
          </wpml:actionActuatorFuncParam>
        </wpml:action>
      </wpml:actionGroup>
    </Placemark>"""


placemark_blocks = "\n".join(placemark(i, lat, lon, alt) for i, (lat, lon, alt) in enumerate(WAYPOINTS))
wayline_blocks   = "\n".join(wayline_point(i, lat, lon, alt) for i, (lat, lon, alt) in enumerate(WAYPOINTS))

template_kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.0">
<Document>
  <wpml:author>WareMan</wpml:author>
  <wpml:createTime>{NOW_MS}</wpml:createTime>
  <wpml:updateTime>{NOW_MS}</wpml:updateTime>
  <wpml:missionConfig>
    <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
    <wpml:finishAction>goHome</wpml:finishAction>
    <wpml:exitOnRCLost>executeLostAction</wpml:exitOnRCLost>
    <wpml:executeRCLostAction>hover</wpml:executeRCLostAction>
    <wpml:globalTransitionalSpeed>{SPEED}</wpml:globalTransitionalSpeed>
    <wpml:droneInfo>
      <wpml:droneEnumValue>67</wpml:droneEnumValue>
      <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
    </wpml:droneInfo>
  </wpml:missionConfig>
  <Folder>
    <wpml:templateType>waypoint</wpml:templateType>
    <wpml:templateId>0</wpml:templateId>
    <wpml:waylineCoordinateSysParam>
      <wpml:coordinateMode>WGS84</wpml:coordinateMode>
      <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
      <wpml:positioningType>GPS</wpml:positioningType>
    </wpml:waylineCoordinateSysParam>
    <wpml:autoFlightSpeed>{SPEED}</wpml:autoFlightSpeed>
{placemark_blocks}
  </Folder>
</Document>
</kml>"""

waylines_wpml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.0">
<Document>
  <Folder>
    <wpml:templateId>0</wpml:templateId>
    <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
    <wpml:waylineId>0</wpml:waylineId>
    <wpml:distance>0</wpml:distance>
    <wpml:duration>0</wpml:duration>
    <wpml:autoFlightSpeed>{SPEED}</wpml:autoFlightSpeed>
{wayline_blocks}
  </Folder>
</Document>
</kml>"""

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("wpmz/template.kml",  template_kml)
    zf.writestr("wpmz/waylines.wpml", waylines_wpml)

output = "test_mission.kmz"
with open(output, "wb") as f:
    f.write(buf.getvalue())

print(f"Creato: {output}")
print(f"Waypoint ({len(WAYPOINTS)}):")
for i, (lat, lon, alt) in enumerate(WAYPOINTS):
    labels = ["Nord", "Est", "Sud", "Ovest"]
    print(f"  WP{i} {labels[i]}: lat={lat:.5f} lon={lon:.5f} alt={alt}m")
print(f"Velocità: {SPEED} m/s — altitudine: {ALT}m relativa al decollo")
