import json

from app.services.ingestion import get_cyclone_by_id
from app.services.infrastructure_exposure import (
    get_map_ready_infrastructure
)


# ============================================================
# MAP-READY OUTPUT
# ============================================================

def build_map_output(
    cyclone_id: str,
    latitude: float,
    longitude: float,
    radius_km: float = 10
):
    """
    Build a single frontend-ready response.

    Combines:
        - cyclone track
        - cyclone information
        - infrastructure assets
        - map metadata

    Hazard/risk values can be attached later
    without changing the infrastructure layer.
    """

    # ========================================================
    # CYCLONE
    # ========================================================

    cyclone = get_cyclone_by_id(
        cyclone_id
    )

    if cyclone is None:

        return {
            "success": False,
            "error": "Cyclone not found"
        }

    # ========================================================
    # INFRASTRUCTURE
    # ========================================================

    infrastructure = (
        get_map_ready_infrastructure(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km
        )
    )

    # ========================================================
    # CYCLONE TRACK
    # ========================================================

    track_features = []

    for index, point in enumerate(
        cyclone.get("track", [])
    ):

        track_features.append({
            "id": index,

            "latitude": point.get(
                "latitude"
            ),

            "longitude": point.get(
                "longitude"
            ),

            "wind_kmph": point.get(
                "wind_kmph"
            ),

            "pressure_hpa": point.get(
                "pressure_hpa"
            ),

            "timestamp": point.get(
                "timestamp"
            )
        })

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        # ----------------------------------------------------
        # MAP CENTER
        # ----------------------------------------------------

        "map": {

            "center": {
                "latitude": latitude,
                "longitude": longitude
            },

            "radius_km": radius_km
        },

        # ----------------------------------------------------
        # CYCLONE
        # ----------------------------------------------------

        "cyclone": {

            "id": cyclone_id,

            "name": cyclone.get(
                "name"
            ),

            "category": cyclone.get(
                "category"
            ),

            "max_wind_kmph": cyclone.get(
                "max_wind_kmph"
            ),

            "min_pressure_hpa": cyclone.get(
                "min_pressure_hpa"
            ),

            "track": track_features
        },

        # ----------------------------------------------------
        # INFRASTRUCTURE
        # ----------------------------------------------------

        "infrastructure": {

            "summary": infrastructure.get(
                "summary",
                {}
            ),

            "exposure": infrastructure.get(
                "exposure",
                {}
            ),

            "features": infrastructure.get(
                "features",
                []
            )
        }
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    latitude = 19.8135
    longitude = 85.8312
    radius_km = 10

    # IMPORTANT:
    # Replace this with the cyclone ID you have
    # already been using for the demo.

    cyclone_id = "CY001"

    print(
        "\n" + "=" * 70
    )

    print(
        "MAP-READY OUTPUT"
    )

    print(
        "=" * 70
    )

    result = build_map_output(
        cyclone_id=cyclone_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )