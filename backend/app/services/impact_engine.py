import math

from app.services.hazard import (
    calculate_wind_hazard,
    calculate_rainfall_hazard,
    calculate_surge_hazard,
    calculate_flood_hazard,
    calculate_combined_hazard,
)

from app.services.vulnerability import (
    calculate_population_vulnerability,
    calculate_infrastructure_vulnerability,
    calculate_agriculture_vulnerability,
    calculate_healthcare_vulnerability,
    calculate_combined_vulnerability,
)

from app.services.risk_engine import (
    calculate_exposure,
    calculate_risk_score,
    classify_risk,
    get_risk_drivers,
)

from app.services.data_sources.location_context import (
    get_location_context,
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate Haversine distance between two coordinates.
    Returns distance in kilometres.
    """

    R = 6371.0

    lat1 = math.radians(
        safe_float(lat1)
    )

    lon1 = math.radians(
        safe_float(lon1)
    )

    lat2 = math.radians(
        safe_float(lat2)
    )

    lon2 = math.radians(
        safe_float(lon2)
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    a = min(
        1.0,
        max(0.0, a)
    )

    return (
        2
        * R
        * math.asin(
            math.sqrt(a)
        )
    )


# ============================================================
# FORECAST POINT EXTRACTION
# ============================================================

def _extract_cyclone_position(forecast_point):
    """
    Extract cyclone latitude/longitude from a forecast point.

    Current track forecast format:

        {
            "cyclone_position": {
                "latitude": ...,
                "longitude": ...
            }
        }

    Older format:

        {
            "latitude": ...,
            "longitude": ...
        }

    Supports both.
    """

    position = forecast_point.get(
        "cyclone_position",
        {}
    )

    if not isinstance(position, dict):
        position = {}

    latitude = position.get(
        "latitude"
    )

    longitude = position.get(
        "longitude"
    )

    # --------------------------------------------------------
    # FALLBACK FOR OLD FLAT FORMAT
    # --------------------------------------------------------

    if latitude is None:
        latitude = forecast_point.get(
            "latitude"
        )

    if longitude is None:
        longitude = forecast_point.get(
            "longitude"
        )

    return (
        safe_float(latitude),
        safe_float(longitude),
    )


def _extract_forecast_metadata(forecast_point):
    """
    Extract forecast timing information.
    """

    hours_ahead = forecast_point.get(
        "hours_ahead"
    )

    forecast_type = forecast_point.get(
        "forecast_type"
    )

    # --------------------------------------------------------
    # OBSERVED POINT
    # --------------------------------------------------------

    if hours_ahead is None:

        hours_ahead = 0

    if forecast_type is None:

        forecast_type = "observed"

    return {
        "hours_ahead": hours_ahead,
        "forecast_type": forecast_type,
        "timestamp": forecast_point.get(
            "timestamp"
        ),
    }


# ============================================================
# MAIN IMPACT ENGINE
# ============================================================

def calculate_point_impact(
    forecast_point,
    target_latitude,
    target_longitude,
):
    """
    Calculate the impact of a cyclone forecast point
    on a target location.

    This function is used by:

        - frontend time slider
        - map point selection
        - future impact API
        - infrastructure impact
        - advisory generation
        - warning generation

    The forecast point may be either:

        OBSERVED
        PROJECTED

    Current forecast structure:

        {
            "timestamp": "...",
            "hours_from_start": 18,
            "hours_ahead": 18,
            "forecast_type": "projected",

            "cyclone_position": {
                "latitude": 18.2,
                "longitude": 83.2
            },

            "wind_kmph": 150,
            "pressure_hpa": 950
        }
    """

    # ========================================================
    # VALIDATE FORECAST POINT
    # ========================================================

    if not isinstance(
        forecast_point,
        dict
    ):
        raise ValueError(
            "forecast_point must be a dictionary"
        )

    # ========================================================
    # FORECAST POSITION
    # ========================================================

    cyclone_lat, cyclone_lon = (
        _extract_cyclone_position(
            forecast_point
        )
    )

    # ========================================================
    # FORECAST METADATA
    # ========================================================

    forecast_metadata = (
        _extract_forecast_metadata(
            forecast_point
        )
    )

    hours_ahead = forecast_metadata[
        "hours_ahead"
    ]

    forecast_type = forecast_metadata[
        "forecast_type"
    ]

    timestamp = forecast_metadata[
        "timestamp"
    ]

    # ========================================================
    # CYCLONE INTENSITY
    # ========================================================

    wind_kmph = safe_float(
        forecast_point.get(
            "wind_kmph"
        )
    )

    pressure_hpa = safe_float(
        forecast_point.get(
            "pressure_hpa"
        )
    )

    # ========================================================
    # LOCATION CONTEXT
    # ========================================================

    location_context = get_location_context(
        target_latitude,
        target_longitude
    )

    rainfall_mm = safe_float(
        location_context.get(
            "rainfall_mm",
            0
        )
    )

    elevation_m = safe_float(
        location_context.get(
            "elevation_m",
            0
        )
    )

    distance_from_coast_km = safe_float(
        location_context.get(
            "distance_from_coast_km",
            0
        )
    )

    population_density = safe_float(
        location_context.get(
            "population_density",
            0
        )
    )

    infrastructure_density = safe_float(
        location_context.get(
            "infrastructure_density",
            0
        )
    )

    agriculture_percentage = safe_float(
        location_context.get(
            "agriculture_percentage",
            0
        )
    )

    healthcare_access = safe_float(
        location_context.get(
            "healthcare_access",
            0
        )
    )

    healthcare_status = location_context.get(
        "healthcare_data_status",
        "unknown"
    )

    # ========================================================
    # DISTANCE FROM CYCLONE
    # ========================================================

    cyclone_distance_km = distance_km(
        cyclone_lat,
        cyclone_lon,
        target_latitude,
        target_longitude
    )

    # ========================================================
    # HAZARD ENGINE
    # ========================================================

    wind_hazard = calculate_wind_hazard(
        cyclone_lat,
        cyclone_lon,
        wind_kmph,
        target_latitude,
        target_longitude
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        wind_kmph,
        distance_from_coast_km,
        elevation_m
    )

    flood_hazard = calculate_flood_hazard(
        rainfall_hazard,
        surge_hazard,
        elevation_m
    )

    combined_hazard = calculate_combined_hazard(
        wind_hazard,
        rainfall_hazard,
        surge_hazard,
        flood_hazard
    )

    # ========================================================
    # HAZARD RESULT
    # ========================================================

    hazards = {

        "wind":
            round(
                safe_float(
                    wind_hazard
                ),
                4
            ),

        "rainfall":
            round(
                safe_float(
                    rainfall_hazard
                ),
                4
            ),

        "storm_surge":
            round(
                safe_float(
                    surge_hazard
                ),
                4
            ),

        "flood":
            round(
                safe_float(
                    flood_hazard
                ),
                4
            ),

        "combined":
            round(
                safe_float(
                    combined_hazard
                ),
                4
            ),
    }

    # ========================================================
    # VULNERABILITY ENGINE
    # ========================================================

    population_vulnerability = (
        calculate_population_vulnerability(
            population_density
        )
    )

    infrastructure_vulnerability = (
        calculate_infrastructure_vulnerability(
            infrastructure_density
        )
    )

    agriculture_vulnerability = (
        calculate_agriculture_vulnerability(
            agriculture_percentage
        )
    )

    healthcare_vulnerability = (
        calculate_healthcare_vulnerability(
            healthcare_access,
            healthcare_status
        )
    )

    combined_vulnerability = (
        calculate_combined_vulnerability(
            population_vulnerability,
            infrastructure_vulnerability,
            agriculture_vulnerability,
            healthcare_vulnerability
        )
    )

    # ========================================================
    # EXPOSURE ENGINE
    # ========================================================

    exposure = calculate_exposure(
        population_density=population_density,

        infrastructure_density=(
            infrastructure_density
        ),

        agriculture_percentage=(
            agriculture_percentage
        )
    )

    # ========================================================
    # RISK ENGINE
    # ========================================================

    risk_score = calculate_risk_score(
        hazard=combined_hazard,
        exposure=exposure,
        vulnerability=combined_vulnerability
    )

    risk_level = classify_risk(
        risk_score
    )

    risk_drivers = get_risk_drivers(
        hazards
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        # ----------------------------------------------------
        # TARGET LOCATION
        # ----------------------------------------------------

        "location": {

            "latitude":
                safe_float(
                    target_latitude
                ),

            "longitude":
                safe_float(
                    target_longitude
                ),
        },

        # ----------------------------------------------------
        # CYCLONE
        # ----------------------------------------------------

        "cyclone": {

            "latitude":
                cyclone_lat,

            "longitude":
                cyclone_lon,

            "distance_km":
                round(
                    cyclone_distance_km,
                    2
                ),

            "wind_kmph":
                wind_kmph,

            "pressure_hpa":
                pressure_hpa,
        },

        # ----------------------------------------------------
        # HAZARDS
        # ----------------------------------------------------

        "hazards":
            hazards,

        # ----------------------------------------------------
        # VULNERABILITY
        # ----------------------------------------------------

        "vulnerability": {

            "population":
                safe_float(
                    population_vulnerability
                ),

            "infrastructure":
                safe_float(
                    infrastructure_vulnerability
                ),

            "agriculture":
                safe_float(
                    agriculture_vulnerability
                ),

            "healthcare":
                safe_float(
                    healthcare_vulnerability
                ),

            "combined":
                safe_float(
                    combined_vulnerability
                ),
        },

        # ----------------------------------------------------
        # EXPOSURE
        # ----------------------------------------------------

        "exposure": {

            "population_density":
                population_density,

            "infrastructure_density":
                infrastructure_density,

            "agriculture_percentage":
                agriculture_percentage,

            "score":
                safe_float(
                    exposure
                ),
        },

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        "risk": {

            "score":
                round(
                    safe_float(
                        risk_score
                    ),
                    4
                ),

            "percentage":
                round(
                    safe_float(
                        risk_score
                    ) * 100,
                    2
                ),

            "level":
                risk_level,

            "drivers":
                risk_drivers,
        },

        # ----------------------------------------------------
        # LOCATION CONTEXT
        # ----------------------------------------------------

        "location_context":
            location_context,

        # ----------------------------------------------------
        # FORECAST
        # ----------------------------------------------------

        "forecast": {

            "hours_ahead":
                hours_ahead,

            "timestamp":
                timestamp,

            "forecast_type":
                forecast_type,
        },
    }