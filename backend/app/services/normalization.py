from typing import Dict, Any


def normalize_cyclone(cyclone: Dict[str, Any]) -> Dict[str, Any]:

    normalized = {
        "id": str(cyclone["id"]),
        "name": cyclone["name"],
        "category": cyclone["category"],
        "max_wind_kmph": float(cyclone["max_wind_kmph"]),
        "min_pressure_hpa": float(cyclone["min_pressure_hpa"]),
        "track": []
    }

    for point in cyclone["track"]:

        normalized["track"].append({
            "timestamp": point["timestamp"],
            "latitude": float(point["latitude"]),
            "longitude": float(point["longitude"]),
            "wind_kmph": float(point["wind_kmph"]),
            "pressure_hpa": float(point["pressure_hpa"])
        })

    return normalized