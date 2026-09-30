import json
import os


HISTORICAL_FILE = "data/historical/odisha_cyclones.json"


def load_historical_cyclones():
    if not os.path.exists(HISTORICAL_FILE):
        return []

    with open(HISTORICAL_FILE, "r") as f:
        data = json.load(f)

    return [
        cyclone
        for cyclone in data
        if cyclone.get("name") != "UNNAMED"
    ]


def get_region_history(region="Odisha"):
    if region.lower() != "odisha":
        return []

    return load_historical_cyclones()


def get_historical_statistics():
    cyclones = load_historical_cyclones()

    if not cyclones:
        return {
            "total_cyclones": 0,
            "cyclones_entering_odisha": 0,
            "average_max_wind_kmph": 0,
            "maximum_wind_kmph": 0,
            "average_min_pressure_hpa": 0,
            "lowest_pressure_hpa": 0
        }

    winds = [
        c["max_wind_kmph"]
        for c in cyclones
        if c.get("max_wind_kmph") is not None
    ]

    pressures = [
        c["min_pressure_hpa"]
        for c in cyclones
        if c.get("min_pressure_hpa") is not None
    ]

    entered_odisha = [
        c
        for c in cyclones
        if c.get("track_intersects_odisha") is True
    ]

    return {
        "total_cyclones": len(cyclones),
        "cyclones_entering_odisha": len(entered_odisha),
        "average_max_wind_kmph": round(
            sum(winds) / len(winds), 1
        ) if winds else 0,
        "maximum_wind_kmph": round(
            max(winds), 1
        ) if winds else 0,
        "average_min_pressure_hpa": round(
            sum(pressures) / len(pressures), 1
        ) if pressures else 0,
        "lowest_pressure_hpa": round(
            min(pressures), 1
        ) if pressures else 0
    }


def calculate_historical_statistics(region="Odisha"):
    if region.lower() != "odisha":
        return {
            "region": region,
            "total_cyclones": 0,
            "cyclones_entering_odisha": 0,
            "message": "Historical dataset currently covers Odisha."
        }

    return {
        "region": "Odisha",
        **get_historical_statistics()
    }


def calculate_similarity(
    cyclone,
    current_wind_kmph,
    current_pressure_hpa
):
    historical_wind = cyclone.get("max_wind_kmph")
    historical_pressure = cyclone.get("min_pressure_hpa")

    if historical_wind is None or historical_pressure is None:
        return None

    wind_difference = abs(
        historical_wind - current_wind_kmph
    )

    pressure_difference = abs(
        historical_pressure - current_pressure_hpa
    )

    wind_score = min(
        wind_difference / 100,
        1.0
    )

    pressure_score = min(
        pressure_difference / 100,
        1.0
    )

    similarity_score = (
        0.6 * wind_score +
        0.4 * pressure_score
    )

    similarity_percentage = (
        1 - similarity_score
    ) * 100

    return round(
        max(
            0,
            min(
                similarity_percentage,
                100
            )
        ),
        2
    )


def find_similar_cyclones(
    current_wind_or_cyclone,
    current_pressure_or_region=None,
    limit=5
):
    cyclones = load_historical_cyclones()

    if isinstance(
        current_wind_or_cyclone,
        (int, float)
    ):
        current_wind_kmph = float(
            current_wind_or_cyclone
        )

        current_pressure_hpa = float(
            current_pressure_or_region
        )

    else:
        cyclone = current_wind_or_cyclone

        latest_point = cyclone["track"][-1]

        current_wind_kmph = latest_point.get(
            "wind_kmph",
            cyclone.get("max_wind_kmph", 0)
        )

        current_pressure_hpa = latest_point.get(
            "pressure_hpa",
            cyclone.get("min_pressure_hpa", 0)
        )

    results = []

    for cyclone in cyclones:

        similarity = calculate_similarity(
            cyclone,
            current_wind_kmph,
            current_pressure_hpa
        )

        if similarity is None:
            continue

        results.append({
            "name": cyclone["name"],
            "year": cyclone["year"],
            "max_wind_kmph": cyclone["max_wind_kmph"],
            "min_pressure_hpa": cyclone["min_pressure_hpa"],
            "minimum_distance_to_odisha_km": cyclone.get(
                "minimum_distance_to_odisha_km"
            ),
            "track_intersects_odisha": cyclone.get(
                "track_intersects_odisha",
                False
            ),
            "similarity_percentage": similarity
        })

    results.sort(
        key=lambda x: x["similarity_percentage"],
        reverse=True
    )

    return results[:limit]


def get_historical_comparison(
    current_wind_kmph,
    current_pressure_hpa
):
    statistics = get_historical_statistics()

    similar_cyclones = find_similar_cyclones(
        current_wind_kmph,
        current_pressure_hpa
    )

    return {
        "statistics": statistics,
        "similar_cyclones": similar_cyclones
    }