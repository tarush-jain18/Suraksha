import math


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:

    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


def calculate_wind_hazard(
    cyclone_lat: float,
    cyclone_lon: float,
    cyclone_wind: float,
    target_lat: float,
    target_lon: float
) -> float:

    distance = calculate_distance(
        cyclone_lat,
        cyclone_lon,
        target_lat,
        target_lon
    )

    decay = math.exp(-distance / 150)

    hazard = (
        cyclone_wind / 200
    ) * decay

    return round(
        max(0.0, min(hazard, 1.0)),
        4
    )


def calculate_rainfall_hazard(
    rainfall_mm: float
) -> float:

    if rainfall_mm < 50:
        hazard = 0.1
    elif rainfall_mm < 100:
        hazard = 0.3
    elif rainfall_mm < 200:
        hazard = 0.6
    elif rainfall_mm < 300:
        hazard = 0.8
    else:
        hazard = 1.0

    return hazard


def calculate_surge_hazard(
    wind_speed: float,
    distance_from_coast_km: float,
    elevation_m: float
) -> float:

    wind_factor = min(wind_speed / 200, 1.0)

    coast_factor = max(
        0.0,
        1.0 - distance_from_coast_km / 100
    )

    elevation_factor = max(
        0.0,
        1.0 - elevation_m / 50
    )

    hazard = (
        0.5 * wind_factor +
        0.3 * coast_factor +
        0.2 * elevation_factor
    )

    return round(
        max(0.0, min(hazard, 1.0)),
        4
    )


def calculate_flood_hazard(
    rainfall_hazard: float,
    surge_hazard: float,
    elevation_m: float
) -> float:

    elevation_factor = max(
        0.0,
        1.0 - elevation_m / 100
    )

    hazard = (
        0.5 * rainfall_hazard +
        0.3 * surge_hazard +
        0.2 * elevation_factor
    )

    return round(
        max(0.0, min(hazard, 1.0)),
        4
    )


def calculate_combined_hazard(
    wind_hazard: float,
    rainfall_hazard: float,
    surge_hazard: float,
    flood_hazard: float
) -> float:

    hazard = (
        0.35 * wind_hazard +
        0.20 * rainfall_hazard +
        0.25 * surge_hazard +
        0.20 * flood_hazard
    )

    return round(hazard, 4)