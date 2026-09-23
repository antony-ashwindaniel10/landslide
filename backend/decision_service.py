# ============================================================
# DECISION SUPPORT
# Infrastructure impact, connectivity, precursors, alerts
# ============================================================

import json
import math
import os
import statistics
import threading
import time
from datetime import datetime, timezone

import pandas as pd
import requests


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(
    BASE_DIR, "data", "processed", "final_ml_dataset_v2.csv"
)
RUNTIME_DIR = os.path.join(BASE_DIR, "data", "runtime")
REPORTS_PATH = os.path.join(RUNTIME_DIR, "citizen_reports.json")
ALERTS_PATH = os.path.join(RUNTIME_DIR, "alerts.json")

_LOCK = threading.Lock()
_OSM_CACHE = {}
_OSM_TTL = 1800

# Demo low-cost sensor nodes placed across NER.
# Live values are derived from the same soil/rainfall observation
# when a prediction is near the node.
IOT_SENSORS = [
    {"id": "IOT-ASS-01", "name": "Guwahati slope node", "latitude": 26.14, "longitude": 91.74},
    {"id": "IOT-MEG-01", "name": "Shillong ridge node", "latitude": 25.57, "longitude": 91.88},
    {"id": "IOT-NAG-01", "name": "Kohima slope node", "latitude": 25.67, "longitude": 94.11},
    {"id": "IOT-MAN-01", "name": "Imphal valley node", "latitude": 24.82, "longitude": 93.95},
    {"id": "IOT-MIZ-01", "name": "Aizawl ridge node", "latitude": 23.73, "longitude": 92.72},
    {"id": "IOT-TRI-01", "name": "Agartala node", "latitude": 23.83, "longitude": 91.28},
    {"id": "IOT-ARU-01", "name": "Itanagar node", "latitude": 27.08, "longitude": 93.61},
    {"id": "IOT-SIK-01", "name": "Gangtok node", "latitude": 27.33, "longitude": 88.61},
]


def _haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _level(score):
    if score >= 75:
        return "Red"
    if score >= 50:
        return "Orange"
    if score >= 25:
        return "Yellow"
    return "Green"


def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_json(path, payload):
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _inventory():
    if not os.path.exists(DATASET_PATH):
        return pd.DataFrame(
            columns=["latitude", "longitude", "slope_degrees", "historical_landslide"]
        )
    frame = pd.read_csv(
        DATASET_PATH,
        usecols=lambda name: name in {
            "latitude",
            "longitude",
            "slope_degrees",
            "elevation_m",
            "historical_landslide",
        },
    )
    return frame


_INVENTORY = _inventory()


def estimate_terrain(latitude, longitude):
    """Slope and elevation from the nearest inventory point when DEM is missing."""
    frame = _INVENTORY.dropna(subset=["latitude", "longitude", "slope_degrees"])
    if frame.empty:
        return {
            "elevation_m": 110.0,
            "slope_degrees": 1.8,
            "source": "Default terrain",
        }

    dlat = frame["latitude"] - latitude
    dlon = (frame["longitude"] - longitude) * math.cos(math.radians(latitude))
    nearest = frame.loc[(dlat ** 2 + dlon ** 2).idxmin()]
    elevation = nearest["elevation_m"] if "elevation_m" in frame.columns else 110.0
    if pd.isna(elevation):
        elevation = 110.0

    return {
        "elevation_m": round(float(elevation), 2),
        "slope_degrees": round(float(nearest["slope_degrees"]), 2),
        "source": "Nearest inventory terrain",
    }


def nearby_landslides(latitude, longitude, radius_km=20):
    if _INVENTORY.empty:
        return []

    positives = _INVENTORY[_INVENTORY["historical_landslide"] == 1]
    hits = []
    for row in positives.itertuples(index=False):
        distance = _haversine_km(
            latitude, longitude, row.latitude, row.longitude
        )
        if distance <= radius_km:
            hits.append({
                "latitude": round(float(row.latitude), 4),
                "longitude": round(float(row.longitude), 4),
                "distance_km": round(distance, 1),
                "slope_degrees": round(float(row.slope_degrees), 1),
            })
    hits.sort(key=lambda item: item["distance_km"])
    return hits[:12]


def build_heatmap():
    if _INVENTORY.empty:
        return []

    positives = _INVENTORY[_INVENTORY["historical_landslide"] == 1].copy()
    if positives.empty:
        return []

    positives["lat_bin"] = (positives["latitude"] / 0.35).round() * 0.35
    positives["lon_bin"] = (positives["longitude"] / 0.35).round() * 0.35
    grouped = positives.groupby(["lat_bin", "lon_bin"], as_index=False).agg(
        count=("latitude", "size"),
        slope=("slope_degrees", "mean"),
    )

    cells = []
    for row in grouped.itertuples(index=False):
        score = min(100, round(row.count * 6 + row.slope * 1.4, 1))
        cells.append({
            "latitude": round(float(row.lat_bin), 3),
            "longitude": round(float(row.lon_bin), 3),
            "landslide_count": int(row.count),
            "mean_slope": round(float(row.slope), 1),
            "risk_score": score,
            "risk_level": _level(score),
        })
    cells.sort(key=lambda item: item["risk_score"], reverse=True)
    return cells


def _nearest_sensor(latitude, longitude):
    nearest = min(
        IOT_SENSORS,
        key=lambda sensor: _haversine_km(
            latitude, longitude, sensor["latitude"], sensor["longitude"]
        ),
    )
    distance = _haversine_km(
        latitude, longitude, nearest["latitude"], nearest["longitude"]
    )
    return nearest, distance


def _reports_near(latitude, longitude, radius_km=15):
    reports = _load_json(REPORTS_PATH)
    nearby = []
    for report in reports:
        distance = _haversine_km(
            latitude,
            longitude,
            report["latitude"],
            report["longitude"],
        )
        if distance <= radius_km:
            item = dict(report)
            item["distance_km"] = round(distance, 1)
            nearby.append(item)
    nearby.sort(key=lambda item: item["distance_km"])
    return nearby[:8]


def analyze_evidence(note, image_bytes=None):
    text = (note or "").lower()
    keywords = [
        word for word in
        ("crack", "debris", "slip", "scarp", "boulder", "subsidence", "seepage")
        if word in text
    ]

    texture = None
    if image_bytes and len(image_bytes) > 500:
        sample = list(image_bytes[:: max(1, len(image_bytes) // 1500)])
        if len(sample) > 2:
            variance = statistics.pvariance(sample)
            texture = "high" if variance > 3500 else "moderate"

    evidence_score = min(
        25,
        len(keywords) * 6 + (8 if texture == "high" else 0),
    )
    return {
        "keywords": keywords,
        "visual_texture": texture,
        "ground_evidence": evidence_score > 0,
        "evidence_score": evidence_score,
        "method": "Keyword and image-texture screen for cracks, debris and slope change",
    }


def save_report(latitude, longitude, note, reporter="Citizen", image_bytes=None):
    analysis = analyze_evidence(note, image_bytes)
    report = {
        "id": f"RPT-{int(time.time())}",
        "latitude": latitude,
        "longitude": longitude,
        "note": note,
        "reporter": reporter,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "synced": True,
    }
    with _LOCK:
        reports = _load_json(REPORTS_PATH)
        reports.append(report)
        _save_json(REPORTS_PATH, reports[-200:])
    return report


def save_alert(latitude, longitude, place, level, score, language, channel):
    alert = {
        "id": f"ALT-{int(time.time())}",
        "latitude": latitude,
        "longitude": longitude,
        "place": place,
        "risk_level": level,
        "risk_score": score,
        "language": language,
        "channel": channel,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        alerts = _load_json(ALERTS_PATH)
        alerts.append(alert)
        _save_json(ALERTS_PATH, alerts[-200:])
    return alert


def list_alerts():
    return list(reversed(_load_json(ALERTS_PATH)))[:20]


def _fetch_infrastructure(latitude, longitude):
    key = f"{round(latitude, 2)}:{round(longitude, 2)}"
    cached = _OSM_CACHE.get(key)
    now = time.time()
    if cached and now - cached[0] < _OSM_TTL:
        return cached[1]

    payload = None
    try:
        query = f"""
        [out:json][timeout:12];
        (
          way(around:7000,{latitude},{longitude})["highway"~"^(trunk|primary|secondary|tertiary)$"];
          node(around:8000,{latitude},{longitude})["place"~"^(village|town|hamlet|city)$"];
          way(around:8000,{latitude},{longitude})["bridge"="yes"];
          node(around:8000,{latitude},{longitude})["amenity"~"^(hospital|clinic|school)$"];
        );
        out tags center 50;
        """
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=14,
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
        payload = _pack_osm(latitude, longitude, elements)
    except Exception:
        payload = None

    if not payload or not payload["roads"]:
        payload = _local_infrastructure(latitude, longitude)

    _OSM_CACHE[key] = (now, payload)
    return payload


def _pack_osm(latitude, longitude, elements):
    roads, villages, bridges, critical = [], [], [], []
    for element in elements:
        tags = element.get("tags") or {}
        center = element.get("center") or {}
        lat = element.get("lat") or center.get("lat")
        lon = element.get("lon") or center.get("lon")
        if lat is None or lon is None:
            continue
        item = {
            "name": tags.get("name") or tags.get("ref") or "Unnamed",
            "latitude": lat,
            "longitude": lon,
            "distance_km": round(
                _haversine_km(latitude, longitude, lat, lon), 1
            ),
        }
        if tags.get("bridge") == "yes":
            item["kind"] = "bridge"
            bridges.append(item)
        elif "highway" in tags:
            item["kind"] = tags.get("highway")
            roads.append(item)
        elif "place" in tags:
            item["kind"] = tags.get("place")
            villages.append(item)
        elif "amenity" in tags:
            item["kind"] = tags.get("amenity")
            critical.append(item)

    return {
        "roads": sorted(roads, key=lambda item: item["distance_km"])[:8],
        "villages": sorted(villages, key=lambda item: item["distance_km"])[:8],
        "bridges": sorted(bridges, key=lambda item: item["distance_km"])[:5],
        "critical": sorted(critical, key=lambda item: item["distance_km"])[:6],
        "source": "OpenStreetMap Overpass",
    }


LOCAL_ASSETS = [
    {"name": "NH-27", "kind": "road", "latitude": 26.14, "longitude": 91.74},
    {"name": "Saraighat Bridge", "kind": "bridge", "latitude": 26.18, "longitude": 91.67},
    {"name": "Guwahati", "kind": "city", "latitude": 26.14, "longitude": 91.74},
    {"name": "GMCH", "kind": "hospital", "latitude": 26.15, "longitude": 91.77},
    {"name": "NH-6", "kind": "road", "latitude": 25.57, "longitude": 91.89},
    {"name": "Shillong", "kind": "city", "latitude": 25.58, "longitude": 91.89},
    {"name": "NH-2", "kind": "road", "latitude": 25.91, "longitude": 93.73},
    {"name": "Kohima", "kind": "city", "latitude": 25.67, "longitude": 94.11},
    {"name": "Dimapur", "kind": "city", "latitude": 25.91, "longitude": 93.72},
    {"name": "NH-102", "kind": "road", "latitude": 24.81, "longitude": 93.94},
    {"name": "Imphal", "kind": "city", "latitude": 24.82, "longitude": 93.95},
    {"name": "NH-306", "kind": "road", "latitude": 23.73, "longitude": 92.72},
    {"name": "Aizawl", "kind": "city", "latitude": 23.73, "longitude": 92.72},
    {"name": "NH-8", "kind": "road", "latitude": 23.83, "longitude": 91.28},
    {"name": "Agartala", "kind": "city", "latitude": 23.83, "longitude": 91.28},
    {"name": "NH-415", "kind": "road", "latitude": 27.10, "longitude": 93.62},
    {"name": "Itanagar", "kind": "city", "latitude": 27.08, "longitude": 93.61},
    {"name": "NH-10", "kind": "road", "latitude": 27.33, "longitude": 88.61},
    {"name": "Gangtok", "kind": "city", "latitude": 27.33, "longitude": 88.61},
    {"name": "NH-15", "kind": "road", "latitude": 26.63, "longitude": 92.80},
    {"name": "Tezpur", "kind": "town", "latitude": 26.63, "longitude": 92.80},
    {"name": "NH-37", "kind": "road", "latitude": 26.75, "longitude": 94.22},
    {"name": "Jorhat", "kind": "town", "latitude": 26.75, "longitude": 94.20},
    {"name": "NH-315", "kind": "road", "latitude": 27.47, "longitude": 94.91},
    {"name": "Dibrugarh", "kind": "city", "latitude": 27.47, "longitude": 94.91},
    {"name": "NH-306A", "kind": "road", "latitude": 24.33, "longitude": 92.67},
    {"name": "Silchar", "kind": "city", "latitude": 24.83, "longitude": 92.78},
]


def _local_infrastructure(latitude, longitude):
    ranked = []
    for asset in LOCAL_ASSETS:
        distance = _haversine_km(
            latitude, longitude, asset["latitude"], asset["longitude"]
        )
        if distance <= 120:
            ranked.append({
                **asset,
                "distance_km": round(distance, 1),
            })
    ranked.sort(key=lambda item: item["distance_km"])

    def take(kinds):
        return [item for item in ranked if item["kind"] in kinds][:6]

    return {
        "roads": take({"road"}),
        "villages": take({"city", "town", "village"}),
        "bridges": take({"bridge"}),
        "critical": take({"hospital", "school", "clinic"}),
        "source": "NER road and settlement register (used when live map data is unavailable)",
    }


def _connectivity(latitude, longitude, infrastructure):
    roads = infrastructure["roads"]
    villages = infrastructure["villages"]
    if not roads:
        return {
            "threatened_segment": None,
            "villages_at_risk_of_isolation": [],
            "alternate_routes": [],
            "evacuation_priority": villages[:3],
            "note": "No mapped highway was found within 7 km.",
        }

    threatened = roads[0]
    isolated = []
    for village in villages:
        nearest_road = min(
            roads,
            key=lambda road: _haversine_km(
                village["latitude"],
                village["longitude"],
                road["latitude"],
                road["longitude"],
            ),
        )
        if nearest_road["name"] == threatened["name"]:
            isolated.append(village["name"])

    alternates = []
    for road in roads[1:]:
        if road["name"] not in alternates and road["name"] != threatened["name"]:
            alternates.append(road["name"])

    return {
        "threatened_segment": threatened,
        "villages_at_risk_of_isolation": isolated[:6],
        "alternate_routes": alternates[:4],
        "evacuation_priority": [village["name"] for village in villages[:4]],
        "note": (
            "Villages whose nearest mapped road is the threatened segment "
            "are treated as at risk of isolation."
        ),
    }


def _alert_text(place, level, score, asset, action):
    return {
        "en": (
            f"Landslide alert for {place}: {level} ({score}/100). "
            f"Threatened: {asset}. Action: {action}"
        ),
        "hi": (
            f"भूस्खलन चेतावनी, {place}: {level} ({score}/100). "
            f"प्रभावित: {asset}. कार्रवाई: {action}"
        ),
        "as": (
            f"ভূমিস্খলন সতৰ্কবাণী, {place}: {level} ({score}/100). "
            f"বিপদত: {asset}. কাৰ্য: {action}"
        ),
    }


def _priority_action(level, connectivity):
    segment = (connectivity.get("threatened_segment") or {}).get("name")
    alternate = ", ".join(connectivity.get("alternate_routes") or []) or "none mapped"
    if level == "Red":
        return (
            f"Close {segment or 'the nearest road'}, evacuate the nearest village, "
            f"and shift traffic to {alternate}."
        )
    if level == "Orange":
        return (
            f"Restrict heavy vehicles on {segment or 'the nearest road'}, "
            "pre-position clearance teams, and warn the nearest village."
        )
    if level == "Yellow":
        return "Inspect drains and the slope face within 24 hours."
    return "Continue monitoring. No immediate closure is indicated."


def build_decision(
    latitude,
    longitude,
    ml_score,
    rainfall_mm,
    soil_wetness,
    slope,
    forecast_rain_72h,
    place_name,
):
    history = nearby_landslides(latitude, longitude)
    reports = _reports_near(latitude, longitude)
    sensor, sensor_distance = _nearest_sensor(latitude, longitude)

    rainfall_signal = min(30, forecast_rain_72h / 4)
    soil_signal = 20 if soil_wetness >= 0.85 else 10 if soil_wetness >= 0.7 else 0
    history_signal = min(15, len(history) * 3)
    report_signal = min(15, sum(item["analysis"]["evidence_score"] for item in reports))
    deform_signal = min(15, (slope / 45) * soil_wetness * 15)
    vegetation_signal = 8 if soil_wetness >= 0.8 and slope >= 20 else 0
    iot_signal = 8 if sensor_distance <= 30 and soil_wetness >= 0.75 else 0

    fused = min(
        100,
        round(
            ml_score * 0.62
            + rainfall_signal
            + soil_signal * 0.5
            + history_signal
            + report_signal * 0.4
            + deform_signal
            + vegetation_signal
            + iot_signal,
            1,
        ),
    )
    level = _level(fused)

    try:
        infrastructure = _fetch_infrastructure(latitude, longitude)
    except Exception:
        infrastructure = {
            "roads": [],
            "villages": [],
            "bridges": [],
            "critical": [],
            "source": "OpenStreetMap unavailable",
        }

    connectivity = _connectivity(latitude, longitude, infrastructure)
    asset = (
        (connectivity.get("threatened_segment") or {}).get("name")
        or (infrastructure["villages"][0]["name"] if infrastructure["villages"] else place_name)
    )
    action = _priority_action(level, connectivity)
    place = place_name or f"{latitude:.3f}, {longitude:.3f}"

    who = [
        {
            "priority": 1,
            "who": infrastructure["villages"][0]["name"] + " village council"
            if infrastructure["villages"] else "Nearest village council",
            "why": "Closest settlement to the slope",
            "channel": "SMS + app",
        },
        {
            "priority": 2,
            "who": "District Emergency Operations Centre",
            "why": "Coordinates evacuation and machinery",
            "channel": "App notification",
        },
    ]
    if infrastructure["roads"]:
        who.append({
            "priority": 3,
            "who": "PWD / road authority",
            "why": f"Road segment {infrastructure['roads'][0]['name']} is threatened",
            "channel": "SMS",
        })
    if level in {"Orange", "Red"}:
        who.append({
            "priority": 4,
            "who": "Public in the affected village",
            "why": "Risk is high enough for a community warning",
            "channel": "SMS + app",
        })

    return {
        "dynamic_score": fused,
        "risk_level": level,
        "answers": {
            "which_slope": (
                f"Slope near {place} "
                f"({slope:.1f}°, soil wetness {soil_wetness:.2f})."
            ),
            "how_severe": f"{level} — dynamic score {fused}/100 (model base {ml_score}).",
            "what_is_affected": asset,
            "who_first": who[0]["who"],
            "what_to_prioritise": action,
        },
        "precursors": [
            {
                "name": "Rainfall accumulation",
                "value": round(forecast_rain_72h, 1),
                "unit": "mm / 72h",
                "signal": round(rainfall_signal, 1),
                "source": "Open-Meteo forecast (IMD feed not configured)",
            },
            {
                "name": "Soil saturation",
                "value": round(soil_wetness, 3),
                "unit": "0–1",
                "signal": soil_signal,
                "source": "NASA POWER GWETTOP",
            },
            {
                "name": "Terrain deformation proxy",
                "value": round(deform_signal, 1),
                "unit": "instability index",
                "signal": round(deform_signal, 1),
                "source": "Slope × saturation proxy until live Sentinel-1 InSAR is connected",
            },
            {
                "name": "Vegetation stress proxy",
                "value": vegetation_signal,
                "unit": "stress index",
                "signal": vegetation_signal,
                "source": "Wet steep-slope proxy until live Sentinel-2 NDVI is connected",
            },
            {
                "name": "Historical landslides nearby",
                "value": len(history),
                "unit": "events within 20 km",
                "signal": history_signal,
                "source": "GSI inventory used in model training",
            },
            {
                "name": "Citizen ground evidence",
                "value": len(reports),
                "unit": "reports within 15 km",
                "signal": report_signal,
                "source": "Geo-tagged citizen reports",
            },
        ],
        "iot": {
            "sensor": sensor,
            "distance_km": round(sensor_distance, 1),
            "in_range": sensor_distance <= 30,
            "fused": iot_signal > 0,
        },
        "historical_landslides": history,
        "citizen_reports": reports,
        "infrastructure": infrastructure,
        "connectivity": connectivity,
        "who_to_warn": who,
        "alerts": _alert_text(place, level, fused, asset, action),
        "priority_action": action,
    }
