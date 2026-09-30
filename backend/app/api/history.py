from fastapi import APIRouter

from app.services.historical import (
    get_region_history,
    calculate_historical_statistics,
    find_similar_cyclones,
    load_historical_cyclones
)


router = APIRouter(
    prefix="/api/history",
    tags=["Historical Data"]
)


@router.get("/{region}")
def get_history(region: str):

    cyclones = get_region_history(region)

    statistics = calculate_historical_statistics(
        region
    )

    return {
        "statistics": statistics,
        "cyclones": cyclones
    }


@router.get("/{region}/compare/{cyclone_id}")
def compare_cyclone(
    region: str,
    cyclone_id: str
):

    # --------------------------------------------------------
    # Validate region
    # --------------------------------------------------------

    if region.lower() != "odisha":

        return {
            "error": "Historical dataset currently covers Odisha only."
        }

    # --------------------------------------------------------
    # Load historical cyclone dataset
    # --------------------------------------------------------

    historical_cyclones = load_historical_cyclones()

    # --------------------------------------------------------
    # Find requested cyclone
    #
    # Supports:
    #   DANA
    #   dana
    #   cyclone SID
    # --------------------------------------------------------

    selected_cyclone = None

    search_id = cyclone_id.strip().lower()

    for cyclone in historical_cyclones:

        name = str(
            cyclone.get("name", "")
        ).strip().lower()

        sid = str(
            cyclone.get("sid", "")
        ).strip().lower()

        if search_id == name or search_id == sid:

            selected_cyclone = cyclone
            break

    # --------------------------------------------------------
    # Cyclone not found
    # --------------------------------------------------------

    if selected_cyclone is None:

        return {
            "error": "Historical cyclone not found",
            "cyclone_id": cyclone_id,
            "region": region
        }

    # --------------------------------------------------------
    # Get historical statistics
    # --------------------------------------------------------

    statistics = calculate_historical_statistics(
        region
    )

    # --------------------------------------------------------
    # Find historically similar cyclones
    #
    # Compare using the selected cyclone's maximum wind
    # and minimum pressure.
    # --------------------------------------------------------

    current_wind = selected_cyclone.get(
        "max_wind_kmph"
    )

    current_pressure = selected_cyclone.get(
        "min_pressure_hpa"
    )

    similar = []

    if (
        current_wind is not None
        and current_pressure is not None
    ):

        similar = find_similar_cyclones(
            current_wind,
            current_pressure,
            limit=6
        )

        # Remove the cyclone being compared itself
        similar = [
            cyclone
            for cyclone in similar
            if not (
                cyclone.get("name") == selected_cyclone.get("name")
                and cyclone.get("year") == selected_cyclone.get("year")
            )
        ]

        # Keep top 5 after removing itself
        similar = similar[:5]

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "success": True,

        "region": region,

        "current_cyclone": {

            "sid": selected_cyclone.get(
                "sid"
            ),

            "name": selected_cyclone.get(
                "name"
            ),

            "year": selected_cyclone.get(
                "year"
            ),

            "max_wind_kmph": selected_cyclone.get(
                "max_wind_kmph"
            ),

            "min_pressure_hpa": selected_cyclone.get(
                "min_pressure_hpa"
            ),

            "minimum_distance_to_odisha_km":
                selected_cyclone.get(
                    "minimum_distance_to_odisha_km"
                ),

            "track_intersects_odisha":
                selected_cyclone.get(
                    "track_intersects_odisha"
                ),

            "track_points":
                selected_cyclone.get(
                    "track_points"
                )
        },

        "historical_statistics": statistics,

        "similar_cyclones": similar
    }