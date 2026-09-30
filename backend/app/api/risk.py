from fastapi import APIRouter

from app.services.ingestion import get_cyclone_by_id

from app.services.alert_engine import (
    generate_alerts,
    generate_track_alerts,
)

from app.services.historical import (
    get_historical_comparison
)

from app.services.track_forecast import (
    calculate_track_risk_forecast
)

from app.services.data_sources.location_context import (
    get_location_context
)

from app.services.vulnerability import (
    calculate_population_vulnerability,
    calculate_infrastructure_vulnerability,
    calculate_agriculture_vulnerability,
    calculate_healthcare_vulnerability,
)

from app.services.hazard import (
    calculate_wind_hazard,
    calculate_rainfall_hazard,
    calculate_surge_hazard,
    calculate_flood_hazard,
    calculate_combined_hazard
)

from app.services.risk_engine import (
    classify_risk,
    calculate_exposure,
    calculate_vulnerability,
    calculate_risk_score,
    get_risk_drivers
)


router = APIRouter(
    prefix="/api/risk",
    tags=["Risk"]
)


@router.get("/{cyclone_id}")
def calculate_risk(
    cyclone_id: str,
    latitude: float,
    longitude: float
):

    # -----------------------------
    # GET CYCLONE
    # -----------------------------

    cyclone = get_cyclone_by_id(
        cyclone_id
    )

    if cyclone is None:
        return {
            "success": False,
            "error": "Cyclone not found"
        }

    # -----------------------------
    # GET LOCATION CONTEXT
    # -----------------------------

    location_context = get_location_context(
        latitude,
        longitude
    )

    rainfall_mm = location_context[
        "rainfall_mm"
    ]

    distance_from_coast_km = location_context[
        "distance_from_coast_km"
    ]

    elevation_m = location_context[
        "elevation_m"
    ]

    population_density = location_context[
        "population_density"
    ]

    infrastructure_density = location_context[
        "infrastructure_density"
    ]

    agriculture_percentage = location_context[
        "agriculture_percentage"
    ]

    healthcare_access = location_context[
        "healthcare_access"
    ]

    # -----------------------------
    # CURRENT CYCLONE POINT
    # -----------------------------

    latest_point = cyclone["track"][-1]

    current_wind_kmph = latest_point[
        "wind_kmph"
    ]

    current_pressure_hpa = latest_point[
        "pressure_hpa"
    ]

    # -----------------------------
    # CURRENT HAZARD
    # -----------------------------

    wind_hazard = calculate_wind_hazard(
        latest_point["latitude"],
        latest_point["longitude"],
        current_wind_kmph,
        latitude,
        longitude
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        current_wind_kmph,
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

    # -----------------------------
    # VULNERABILITY
    # -----------------------------

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
            healthcare_access
        )
    )

    combined_vulnerability = (
        calculate_vulnerability(
            population_vulnerability,
            infrastructure_vulnerability,
            agriculture_vulnerability,
            healthcare_vulnerability
        )
    )

    # -----------------------------
    # EXPOSURE
    # -----------------------------

    exposure = calculate_exposure(
        population_density=population_density,
        infrastructure_density=(
            infrastructure_density
        ),
        agriculture_percentage=(
            agriculture_percentage
        )
    )

    # -----------------------------
    # CURRENT RISK
    # -----------------------------

    impact_risk = calculate_risk_score(
        hazard=combined_hazard,
        exposure=exposure,
        vulnerability=combined_vulnerability
    )

    risk_level = classify_risk(
        impact_risk
    )

    # -----------------------------
    # RISK DRIVERS
    # -----------------------------

    hazards = {
        "wind": wind_hazard,
        "rainfall": rainfall_hazard,
        "storm_surge": surge_hazard,
        "flood": flood_hazard
    }

    risk_drivers = get_risk_drivers(
        hazards
    )

    # -----------------------------
    # CURRENT ALERTS
    # -----------------------------

    alerts = generate_alerts(
        impact_risk,
        hazards
    )

    # -----------------------------
    # HISTORICAL
    # -----------------------------

    historical_comparison = (
        get_historical_comparison(
            current_wind_kmph,
            current_pressure_hpa
        )
    )

    # -----------------------------
    # TRACK FORECAST
    # -----------------------------

    track_forecast = (
        calculate_track_risk_forecast(
            track=cyclone["track"],
            target_latitude=latitude,
            target_longitude=longitude,
            rainfall_mm=rainfall_mm,
            distance_from_coast_km=(
                distance_from_coast_km
            ),
            elevation_m=elevation_m,
            exposure=exposure,
            vulnerability=combined_vulnerability,
        )
    )

    # -----------------------------
    # TRACK ALERTS
    # -----------------------------

    track_alerts = generate_track_alerts(
        cyclone_name=cyclone["name"],
        target_location=f"{latitude}, {longitude}",
        track_forecast=track_forecast
    )

    # -----------------------------
    # RESPONSE
    # -----------------------------

    return {
        "success": True,

        "cyclone_id": cyclone_id,

        "cyclone": {
            "name": cyclone["name"],
            "category": cyclone["category"],
            "max_wind_kmph": cyclone[
                "max_wind_kmph"
            ],
            "min_pressure_hpa": cyclone[
                "min_pressure_hpa"
            ]
        },

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "location_context": location_context,

        "current_conditions": {
            "wind_kmph": current_wind_kmph,
            "pressure_hpa": current_pressure_hpa
        },

        "hazards": {
            "wind": wind_hazard,
            "rainfall": rainfall_hazard,
            "storm_surge": surge_hazard,
            "flood": flood_hazard,
            "combined": combined_hazard
        },

        "exposure": {
            "population_density": population_density,
            "infrastructure_density": (
                infrastructure_density
            ),
            "agriculture_percentage": (
                agriculture_percentage
            ),
            "score": exposure
        },

        "vulnerability": {
            "population": (
                population_vulnerability
            ),
            "infrastructure": (
                infrastructure_vulnerability
            ),
            "agriculture": (
                agriculture_vulnerability
            ),
            "healthcare": (
                healthcare_vulnerability
            ),
            "combined": combined_vulnerability
        },

        "impact": {
            "risk_score": impact_risk,
            "risk_percentage": round(
                impact_risk * 100,
                2
            ),
            "risk_level": risk_level,
            "drivers": risk_drivers
        },

        "track_forecast": track_forecast,

        "historical": (
            historical_comparison
        ),

        "alerts": alerts,

        "track_alerts": track_alerts
    }