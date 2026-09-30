from fastapi import APIRouter, Query

from app.services.data_sources.current_cyclone import get_current_imd_data
from app.services.data_sources.location_context import get_location_context

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
    classify_risk,
    get_risk_drivers,
)

from app.services.historical import (
    get_historical_statistics,
    get_historical_comparison,
)


router = APIRouter(
    prefix="/api/cyclones",
    tags=["Current Cyclone"]
)


DEFAULT_LATITUDE = 19.8135
DEFAULT_LONGITUDE = 85.8312


@router.get("/current")
def current_cyclone():
    return get_current_imd_data()


@router.get("/current/odisha-impact")
def current_odisha_impact(
    latitude: float = Query(DEFAULT_LATITUDE),
    longitude: float = Query(DEFAULT_LONGITUDE),
):

    current_data = get_current_imd_data()

    location_context = get_location_context(
        latitude=latitude,
        longitude=longitude
    )

    systems = current_data.get(
        "odisha_systems",
        []
    )

    historical_statistics = (
        get_historical_statistics()
    )

    if not systems:

        return {
            "success": True,

            "status": "NO_CURRENT_ODISHA_SYSTEM",

            "region": "Odisha",

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "message": (
                "No current cyclone or cyclone system "
                "is currently identified as relevant to Odisha."
            ),

            "risk_calculation": False,

            "location_context": location_context,

            "historical_context": {
                "statistics": historical_statistics,
                "similar_cyclones": []
            },

            "systems": []
        }

    system = systems[0]

    track = system.get(
        "track",
        []
    )

    if not track:

        return {
            "success": True,

            "status": (
                "ODISHA_SYSTEM_TRACK_UNAVAILABLE"
            ),

            "region": "Odisha",

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "message": (
                "A cyclone system relevant to Odisha "
                "was detected, but a usable track is "
                "not currently available."
            ),

            "risk_calculation": False,

            "location_context": location_context,

            "historical_context": {
                "statistics": historical_statistics,
                "similar_cyclones": []
            },

            "systems": systems
        }

    latest = track[-1]

    cyclone_lat = latest.get(
        "latitude"
    )

    cyclone_lon = latest.get(
        "longitude"
    )

    wind_kmph = latest.get(
        "wind_kmph",
        system.get(
            "max_wind_kmph",
            0
        )
    )

    pressure_hpa = latest.get(
        "pressure_hpa",
        system.get(
            "min_pressure_hpa",
            1013
        )
    )

    if (
        cyclone_lat is None
        or cyclone_lon is None
    ):

        return {
            "success": True,

            "status": (
                "ODISHA_SYSTEM_TRACK_UNAVAILABLE"
            ),

            "region": "Odisha",

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "message": (
                "Cyclone information is available, "
                "but the current system does not have "
                "usable coordinates for risk calculation."
            ),

            "risk_calculation": False,

            "location_context": location_context,

            "historical_context": {
                "statistics": historical_statistics,
                "similar_cyclones": []
            },

            "systems": systems
        }

    rainfall_mm = location_context.get(
        "rainfall_mm",
        0
    )

    elevation_m = location_context.get(
        "elevation_m",
        0
    )

    distance_from_coast_km = (
        location_context.get(
            "distance_from_coast_km",
            100
        )
    )

    population_density = (
        location_context.get(
            "population_density",
            0
        )
    )

    infrastructure_density = (
        location_context.get(
            "infrastructure_density",
            0
        )
    )

    agriculture_percentage = (
        location_context.get(
            "agriculture_percentage",
            0
        )
    )

    healthcare_access = (
        location_context.get(
            "healthcare_access"
        )
    )

    healthcare_status = (
        location_context.get(
            "healthcare_data_status",
            "unknown"
        )
    )

    wind_hazard = calculate_wind_hazard(
        cyclone_lat=cyclone_lat,
        cyclone_lon=cyclone_lon,
        cyclone_wind=wind_kmph,
        target_lat=latitude,
        target_lon=longitude
    )

    rainfall_hazard = (
        calculate_rainfall_hazard(
            rainfall_mm
        )
    )

    surge_hazard = calculate_surge_hazard(
        wind_speed=wind_kmph,
        distance_from_coast_km=(
            distance_from_coast_km
        ),
        elevation_m=elevation_m
    )

    flood_hazard = calculate_flood_hazard(
        rainfall_hazard=rainfall_hazard,
        surge_hazard=surge_hazard,
        elevation_m=elevation_m
    )

    combined_hazard = (
        calculate_combined_hazard(
            wind_hazard=wind_hazard,
            rainfall_hazard=rainfall_hazard,
            surge_hazard=surge_hazard,
            flood_hazard=flood_hazard
        )
    )

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

    if healthcare_access is None:

        return {
            "success": True,

            "status": (
                "ODISHA_SYSTEM_HEALTHCARE_DATA_UNAVAILABLE"
            ),

            "region": "Odisha",

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "risk_calculation": False,

            "message": (
                "A cyclone relevant to Odisha is active, "
                "but healthcare vulnerability data is "
                "currently unavailable."
            ),

            "location_context": location_context,

            "hazards": {
                "wind": wind_hazard,
                "rainfall": rainfall_hazard,
                "storm_surge": surge_hazard,
                "flood": flood_hazard,
                "combined": combined_hazard
            },

            "vulnerability": {
                "population": population_vulnerability,
                "infrastructure": (
                    infrastructure_vulnerability
                ),
                "agriculture": (
                    agriculture_vulnerability
                ),
                "healthcare": None,
                "combined": None
            },

            "risk": {
                "score": None,
                "percentage": None,
                "level": "UNAVAILABLE",
                "drivers": [
                    "Healthcare vulnerability data unavailable"
                ]
            },

            "historical_context": {
                "statistics": historical_statistics,
                "similar_cyclones": []
            },

            "system": system
        }

    healthcare_vulnerability = (
        calculate_healthcare_vulnerability(
            healthcare_access
        )
    )

    combined_vulnerability = (
        calculate_combined_vulnerability(
            population=population_vulnerability,
            infrastructure=(
                infrastructure_vulnerability
            ),
            agriculture=(
                agriculture_vulnerability
            ),
            healthcare=(
                healthcare_vulnerability
            )
        )
    )

    risk_score = (
        combined_hazard
        * combined_vulnerability
    )

    risk_percentage = round(
        risk_score * 100,
        2
    )

    risk_level = classify_risk(
        risk_score
    )

    hazards = {
        "wind": wind_hazard,
        "rainfall": rainfall_hazard,
        "storm_surge": surge_hazard,
        "flood": flood_hazard
    }

    drivers = get_risk_drivers(
        hazards
    )

    historical = get_historical_comparison(
        current_wind_kmph=wind_kmph,
        current_pressure_hpa=pressure_hpa
    )

    return {
        "success": True,

        "status": "ODISHA_SYSTEM_ACTIVE",

        "region": "Odisha",

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "cyclone": {
            "id": system.get("id"),
            "name": system.get("name"),
            "category": system.get("category"),
            "current_wind_kmph": wind_kmph,
            "current_pressure_hpa": pressure_hpa,
            "latitude": cyclone_lat,
            "longitude": cyclone_lon
        },

        "risk_calculation": True,

        "hazards": {
            "wind": wind_hazard,
            "rainfall": rainfall_hazard,
            "storm_surge": surge_hazard,
            "flood": flood_hazard,
            "combined": combined_hazard
        },

        "vulnerability": {
            "population": population_vulnerability,
            "infrastructure": (
                infrastructure_vulnerability
            ),
            "agriculture": (
                agriculture_vulnerability
            ),
            "healthcare": (
                healthcare_vulnerability
            ),
            "combined": (
                combined_vulnerability
            )
        },

        "risk": {
            "score": round(
                risk_score,
                4
            ),
            "percentage": risk_percentage,
            "level": risk_level,
            "drivers": drivers
        },

        "healthcare": {
            "access": healthcare_access,
            "facilities": location_context.get(
                "healthcare_facilities"
            ),
            "nearest_km": location_context.get(
                "nearest_healthcare_km"
            ),
            "status": healthcare_status,
            "facilities_list": location_context.get(
                "healthcare_facilities_list",
                []
            )
        },

        "historical_context": historical,

        "location_context": location_context,

        "system": system
    }