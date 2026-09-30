from fastapi import APIRouter, HTTPException

from app.services.track_forecast import calculate_track_risk_forecast
from app.services.impact_engine import calculate_point_impact
from app.services.infrastructure_exposure import (
    calculate_infrastructure_exposure,
)
from app.services.authority_gemini_advisory import (
    generate_authority_advisory,
)

from app.services.early_warning_trigger import (
    evaluate_early_warning_trigger,
)

from app.services.early_warning_monitor import (
    get_monitor_status,
    start_monitor,
    stop_monitor,
)
from app.services.dispatch_engine import dispatch_authority_advisory
from app.services.dispatch_state import record_dispatch, get_dispatch_state
from app.services.ingestion import get_cyclone_by_id
from app.services.data_sources.location_context import get_location_context
from app.services.historical import (
    calculate_historical_statistics,
    find_similar_cyclones
)

from app.services.risk_engine import (
    classify_risk,
    get_risk_drivers,
    calculate_risk_score,
    calculate_exposure,
    calculate_vulnerability
)

from app.services.alert_engine import generate_alerts

from app.services.hazard import (
    calculate_wind_hazard,
    calculate_rainfall_hazard,
    calculate_surge_hazard,
    calculate_flood_hazard,
    calculate_combined_hazard
)

from app.services.vulnerability import (
    calculate_population_vulnerability,
    calculate_infrastructure_vulnerability,
    calculate_agriculture_vulnerability,
    calculate_healthcare_vulnerability,
    calculate_combined_vulnerability
)
from app.services.forecast_summary import (
    generate_forecast_summary
)


router = APIRouter(
    prefix="/api/cyclones",
    tags=["Cyclones"]
)


@router.get("/")
def get_cyclones():

    cyclone = get_cyclone_by_id("CY001")

    if cyclone is None:
        raise HTTPException(
            status_code=404,
            detail="No cyclones found"
        )

    return {
        "count": 1,
        "cyclones": [cyclone]
    }

@router.get("/{cyclone_id}/track")
def get_cyclone_track(
    cyclone_id: str,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
):
    """
    Return observed + projected cyclone track
    with hazard and risk information.
    """

    # --------------------------------------------------------
    # GET CYCLONE
    # --------------------------------------------------------

    cyclone = get_cyclone_by_id(
        cyclone_id
    )

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found",
        )

    # --------------------------------------------------------
    # LOCATION CONTEXT
    # --------------------------------------------------------

    location_context = get_location_context(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # TRACK FORECAST
    # --------------------------------------------------------

    forecast = calculate_track_risk_forecast(

        track=cyclone["track"],

        target_latitude=latitude,

        target_longitude=longitude,

        rainfall_mm=location_context.get(
            "rainfall_mm",
            0
        ),

        distance_from_coast_km=location_context.get(
            "distance_from_coast_km",
            0
        ),

        elevation_m=location_context.get(
            "elevation_m",
            0
        ),

        exposure=1.0,

        vulnerability=1.0,
    )

    timeline = forecast.get(
        "timeline",
        []
    )

    # --------------------------------------------------------
    # SEPARATE OBSERVED / PROJECTED
    # --------------------------------------------------------

    observed = [
        point
        for point in timeline
        if point.get(
            "forecast_type"
        ) == "observed"
    ]

    projected = [
        point
        for point in timeline
        if point.get(
            "forecast_type"
        ) == "projected"
    ]

    # --------------------------------------------------------
    # MAP-READY TRACK
    # --------------------------------------------------------

    map_track = []

    for point in timeline:

        position = point.get(
            "cyclone_position",
            {}
        )

        map_track.append({

            "latitude":
                position.get(
                    "latitude"
                ),

            "longitude":
                position.get(
                    "longitude"
                ),

            "timestamp":
                point.get(
                    "timestamp"
                ),

            "hours_from_start":
                point.get(
                    "hours_from_start"
                ),

            "hours_ahead":
                point.get(
                    "hours_ahead",
                    0
                ),

            "forecast_type":
                point.get(
                    "forecast_type",
                    "observed"
                ),

            "wind_kmph":
                point.get(
                    "wind_kmph"
                ),

            "pressure_hpa":
                point.get(
                    "pressure_hpa"
                ),

            "distance_to_location_km":
                point.get(
                    "distance_to_location_km"
                ),

            "hazards":
                point.get(
                    "hazards",
                    {}
                ),

            "risk":
                point.get(
                    "risk",
                    {}
                ),
        })

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "cyclone_id":
            cyclone_id,

        "cyclone_name":
            cyclone.get(
                "name",
                cyclone_id
            ),

        "target": {

            "latitude":
                latitude,

            "longitude":
                longitude,
        },

        "observed_points":
            len(observed),

        "projected_points":
            len(projected),

        "track":
            map_track,

        "peak":
            forecast.get(
                "peak"
            ),

        "closest_approach":
            forecast.get(
                "closest_approach"
            ),
    }

@router.get("/{cyclone_id}/infrastructure")
def get_cyclone_infrastructure(
    cyclone_id: str,
    hours: int = 18,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
    radius_km: float = 10,
):
    """
    Return infrastructure exposure for a selected
    cyclone forecast hour.

    Example:

        /api/cyclones/CY001/infrastructure?hours=18
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    allowed_hours = [
        6,
        12,
        18,
        24,
        30,
        36,
    ]

    if hours not in allowed_hours:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Unsupported forecast hour",

                "allowed_hours":
                    allowed_hours,
            },
        )

    if radius_km <= 0:

        raise HTTPException(
            status_code=400,
            detail="radius_km must be greater than 0",
        )

    # ========================================================
    # GET CYCLONE
    # ========================================================

    cyclone = get_cyclone_by_id(
        cyclone_id
    )

    if not cyclone:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Cyclone {cyclone_id} "
                "not found"
            ),
        )

    # ========================================================
    # LOCATION CONTEXT
    # ========================================================

    location_context = get_location_context(
        latitude,
        longitude,
    )

    # ========================================================
    # TRACK FORECAST
    # ========================================================

    forecast = calculate_track_risk_forecast(

        track=cyclone["track"],

        target_latitude=latitude,

        target_longitude=longitude,

        rainfall_mm=location_context.get(
            "rainfall_mm",
            0,
        ),

        distance_from_coast_km=location_context.get(
            "distance_from_coast_km",
            0,
        ),

        elevation_m=location_context.get(
            "elevation_m",
            0,
        ),

        exposure=1.0,

        vulnerability=1.0,
    )

    timeline = forecast.get(
        "timeline",
        [],
    )

    # ========================================================
    # FIND PROJECTED FORECAST POINT
    # ========================================================

    forecast_point = next(
        (
            point
            for point in timeline
            if point.get(
                "forecast_type"
            ) == "projected"
            and point.get(
                "hours_ahead"
            ) == hours
        ),
        None,
    )

    if forecast_point is None:

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "Projected forecast point not found",

                "cyclone_id":
                    cyclone_id,

                "hours":
                    hours,
            },
        )

    # ========================================================
    # IMPACT OF THIS FORECAST POINT
    # ========================================================

    impact = calculate_point_impact(
        forecast_point,
        latitude,
        longitude,
    )

    # ========================================================
    # INFRASTRUCTURE EXPOSURE
    # ========================================================

    infrastructure = (
        calculate_infrastructure_exposure(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "cyclone_id":
            cyclone_id,

        "cyclone_name":
            cyclone.get(
                "name",
                cyclone_id,
            ),

        "target": {

            "latitude":
                latitude,

            "longitude":
                longitude,
        },

        "forecast": {

            "hours_ahead":
                hours,

            "timestamp":
                forecast_point.get(
                    "timestamp"
                ),

            "forecast_type":
                forecast_point.get(
                    "forecast_type"
                ),

            "cyclone_position":
                forecast_point.get(
                    "cyclone_position",
                    {},
                ),
        },

        "impact": {

            "cyclone":
                impact.get(
                    "cyclone",
                    {},
                ),

            "hazards":
                impact.get(
                    "hazards",
                    {},
                ),

            "risk":
                impact.get(
                    "risk",
                    {},
                ),
        },

        "infrastructure": {

            "summary":
                infrastructure.get(
                    "summary",
                    {},
                ),

            "exposure":
                infrastructure.get(
                    "exposure",
                    {},
                ),

            "categories":
                infrastructure.get(
                    "categories",
                    {},
                ),

            "assets":
                infrastructure.get(
                    "assets",
                    [],
                ),
        },
    }

@router.get("/{cyclone_id}")
def get_cyclone(cyclone_id: str):

    cyclone = get_cyclone_by_id(cyclone_id)

    if cyclone is None:
        raise HTTPException(
            status_code=404,
            detail="Cyclone not found"
        )

    return cyclone

@router.get("/{cyclone_id}/forecast")
def get_forecast(
    cyclone_id: str,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
    region: str = "Odisha"
):

    cyclone = get_cyclone_by_id(cyclone_id)

    if cyclone is None:
        raise HTTPException(
            status_code=404,
            detail="Cyclone not found"
        )

    latest_point = cyclone["track"][-1]

    location_context = get_location_context(
        latitude,
        longitude
    )

    rainfall_mm = location_context["rainfall_mm"]
    elevation_m = location_context["elevation_m"]
    distance_from_coast_km = location_context["distance_from_coast_km"]

    population_density = location_context["population_density"]
    infrastructure_density = location_context["infrastructure_density"]
    agriculture_percentage = location_context["agriculture_percentage"]
    healthcare_access = location_context["healthcare_access"]
    healthcare_data_status = location_context["healthcare_data_status"]
    # -------------------------
    # HAZARDS
    # -------------------------

    wind_hazard = calculate_wind_hazard(
        latest_point["latitude"],
        latest_point["longitude"],
        latest_point["wind_kmph"],
        latitude,
        longitude
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        latest_point["wind_kmph"],
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

    # -------------------------
    # VULNERABILITY
    # -------------------------

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
            healthcare_data_status
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

    # -------------------------
    # IMPACT
    # -------------------------

    impact_risk = (
        combined_hazard *
        combined_vulnerability
    )

    risk_level = classify_risk(
        impact_risk
    )

    hazards = {
        "wind": wind_hazard,
        "rainfall": rainfall_hazard,
        "storm_surge": surge_hazard,
        "flood": flood_hazard
    }

    risk_drivers = get_risk_drivers(
        hazards
    )

    # -------------------------
    # ALERTS
    # -------------------------

    alerts = generate_alerts(
        impact_risk,
        hazards
    )

    # -------------------------
    # HISTORY
    # -------------------------

    historical_statistics = (
        calculate_historical_statistics(
            region
        )
    )

    similar_cyclones = find_similar_cyclones(
        cyclone,
        region
    )
    forecast_summary = generate_forecast_summary(
    cyclone,
    {
        "risk_percentage": round(
            impact_risk * 100,
            2
        ),
        "risk_level": risk_level
    },
    alerts,
    {
        "similar_cyclones": similar_cyclones
    }
    )
    # -------------------------
    # RESPONSE
    # -------------------------

    return {

        "cyclone": {
            "id": cyclone["id"],
            "name": cyclone["name"],
            "category": cyclone["category"],
            "max_wind_kmph": cyclone["max_wind_kmph"],
            "min_pressure_hpa": cyclone["min_pressure_hpa"],
            "latest_position": {
                "latitude": latest_point["latitude"],
                "longitude": latest_point["longitude"]
            },
            "track": cyclone["track"]
        },

        "hazards": {
            "wind": wind_hazard,
            "rainfall": rainfall_hazard,
            "storm_surge": surge_hazard,
            "flood": flood_hazard,
            "combined": combined_hazard
        },

        "vulnerability": {
            "population": population_vulnerability,
            "infrastructure": infrastructure_vulnerability,
            "agriculture": agriculture_vulnerability,
            "healthcare": healthcare_vulnerability,
            "combined": combined_vulnerability
        },

        "impact": {
            "risk_score": round(
                impact_risk,
                4
            ),
            "risk_percentage": round(
                impact_risk * 100,
                2
            ),
            "risk_level": risk_level,
            "drivers": risk_drivers
        },

        "alerts": alerts,
        "summary": forecast_summary,

        "historical": {
            "region": region,
            "statistics": historical_statistics,
            "similar_cyclones": similar_cyclones
        }
    }


@router.get("/{cyclone_id}/impact/{hours}")
def get_cyclone_impact(
    cyclone_id: str,
    hours: int,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
):
    """
    Return cyclone impact for a specific future forecast hour.

    Example:

        /api/cyclones/CY001/impact/18
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    allowed_hours = [6, 12, 18, 24, 30, 36]

    if hours not in allowed_hours:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported forecast hour",
                "allowed_hours": allowed_hours,
            },
        )

    # --------------------------------------------------------
    # GET CYCLONE
    # --------------------------------------------------------

    cyclone = get_cyclone_by_id(
        cyclone_id
    )

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found",
        )

    # --------------------------------------------------------
    # LOCATION CONTEXT
    # --------------------------------------------------------

    location_context = get_location_context(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # TRACK FORECAST
    # --------------------------------------------------------

    forecast = calculate_track_risk_forecast(

        track=cyclone["track"],

        target_latitude=latitude,

        target_longitude=longitude,

        rainfall_mm=location_context.get(
            "rainfall_mm",
            0
        ),

        distance_from_coast_km=location_context.get(
            "distance_from_coast_km",
            0
        ),

        elevation_m=location_context.get(
            "elevation_m",
            0
        ),

        exposure=1.0,

        vulnerability=1.0,
    )

    timeline = forecast.get(
        "timeline",
        []
    )

    # --------------------------------------------------------
    # FIND PROJECTED POINT
    # --------------------------------------------------------

    forecast_point = next(
        (
            point
            for point in timeline
            if point.get("forecast_type") == "projected"
            and point.get("hours_ahead") == hours
        ),
        None,
    )

    if forecast_point is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Forecast point not found",
                "cyclone_id": cyclone_id,
                "hours": hours,
            },
        )

    # --------------------------------------------------------
    # CALCULATE IMPACT
    # --------------------------------------------------------

    impact = calculate_point_impact(
        forecast_point,
        latitude,
        longitude,
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "cyclone_id": cyclone_id,

        "cyclone_name": cyclone.get(
            "name",
            cyclone_id
        ),

        "target": {
            "latitude": latitude,
            "longitude": longitude,
        },

        "forecast_hour": hours,

        "impact": impact,
    }

@router.get("/{cyclone_id}/map")
def get_map_ready_output(
    cyclone_id: str,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
    radius_km: float = 10,
):
    """
    Return frontend-ready map data.

    Includes:
    - observed cyclone track
    - projected cyclone track
    - target location
    - risk information
    - infrastructure exposure
    """

    # --------------------------------------------------------
    # GET CYCLONE
    # --------------------------------------------------------

    cyclone = get_cyclone_by_id(cyclone_id)

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found",
        )

    # --------------------------------------------------------
    # LOCATION CONTEXT
    # --------------------------------------------------------

    location_context = get_location_context(
        latitude,
        longitude,
    )

    # --------------------------------------------------------
    # TRACK FORECAST
    # --------------------------------------------------------

    forecast = calculate_track_risk_forecast(

        track=cyclone["track"],

        target_latitude=latitude,

        target_longitude=longitude,

        rainfall_mm=location_context.get(
            "rainfall_mm",
            0,
        ),

        distance_from_coast_km=location_context.get(
            "distance_from_coast_km",
            0,
        ),

        elevation_m=location_context.get(
            "elevation_m",
            0,
        ),

        exposure=1.0,

        vulnerability=1.0,
    )

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    timeline = forecast.get(
        "timeline",
        [],
    )

    observed = [
        point
        for point in timeline
        if point.get("forecast_type") == "observed"
    ]

    projected = [
        point
        for point in timeline
        if point.get("forecast_type") == "projected"
    ]

    # --------------------------------------------------------
    # MAP-READY TRACK
    # --------------------------------------------------------

    observed_coordinates = []

    projected_coordinates = []

    map_points = []

    for point in timeline:

        position = point.get(
            "cyclone_position",
            {},
        )

        latitude_point = position.get(
            "latitude"
        )

        longitude_point = position.get(
            "longitude"
        )

        if latitude_point is None or longitude_point is None:
            continue

        coordinate = [
            longitude_point,
            latitude_point,
        ]

        if point.get("forecast_type") == "observed":

            observed_coordinates.append(
                coordinate
            )

        else:

            projected_coordinates.append(
                coordinate
            )

        map_points.append({
            "latitude": latitude_point,

            "longitude": longitude_point,

            "timestamp": point.get(
                "timestamp"
            ),

            "hours_from_start": point.get(
                "hours_from_start"
            ),

            "hours_ahead": point.get(
                "hours_ahead",
                0,
            ),

            "forecast_type": point.get(
                "forecast_type",
                "observed",
            ),

            "wind_kmph": point.get(
                "wind_kmph"
            ),

            "pressure_hpa": point.get(
                "pressure_hpa"
            ),

            "distance_to_location_km": point.get(
                "distance_to_location_km"
            ),

            "hazards": point.get(
                "hazards",
                {},
            ),

            "risk": point.get(
                "risk",
                {},
            ),
        })

    # --------------------------------------------------------
    # INFRASTRUCTURE
    # --------------------------------------------------------

    infrastructure = calculate_infrastructure_exposure(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    peak = forecast.get(
        "peak",
        {},
    )

    peak_risk = peak.get(
        "risk_score",
        0,
    )

    peak_hazards = {}

    if timeline:

        highest_risk_point = max(
            timeline,
            key=lambda point: point.get(
                "risk",
                {}
            ).get(
                "score",
                0,
            ),
        )

        peak_hazards = highest_risk_point.get(
            "hazards",
            {},
        )

    alerts = generate_alerts(
        peak_risk,
        peak_hazards,
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "cyclone": {

            "id": cyclone_id,

            "name": cyclone.get(
                "name",
                cyclone_id,
            ),

            "category": cyclone.get(
                "category"
            ),
        },

        "target": {

            "latitude": latitude,

            "longitude": longitude,
        },

        "map": {

            "center": {

                "latitude": latitude,

                "longitude": longitude,
            },

            "track": {

                "observed": {

                    "type": "LineString",

                    "coordinates":
                        observed_coordinates,
                },

                "projected": {

                    "type": "LineString",

                    "coordinates":
                        projected_coordinates,
                },

                "all_points": map_points,
            },

            "target_marker": {

                "type": "Point",

                "coordinates": [
                    longitude,
                    latitude,
                ],
            },

            "peak_risk": peak,

            "infrastructure":
                infrastructure,

            "alerts":
                alerts,

            "layers": {

                "cyclone_track": True,

                "projected_track": True,

                "risk": True,

                "hazards": True,

                "infrastructure": True,

                "alerts": True,

                "target": True,
            },
        },
    }
# ============================================================
# AUTHORITY EARLY-WARNING API
# ============================================================
@router.get("/{cyclone_id}/warning")
def get_cyclone_warning(
    cyclone_id: str,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
):
    cyclone = get_cyclone_by_id(cyclone_id)

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found"
        )

    # ------------------------------------------------------------
    # LOCATION CONTEXT
    # ------------------------------------------------------------

    location_context = get_location_context(
        latitude,
        longitude
    )

    rainfall_mm = float(
        location_context.get("rainfall_mm", 0)
    )

    distance_from_coast_km = float(
        location_context.get("distance_from_coast_km", 0)
    )

    elevation_m = float(
        location_context.get("elevation_m", 0)
    )

    population_density = float(
        location_context.get("population_density", 0)
    )

    infrastructure_density = float(
        location_context.get("infrastructure_density", 0)
    )

    agriculture_percentage = float(
        location_context.get("agriculture_percentage", 0)
    )

    # ------------------------------------------------------------
    # CURRENT HAZARDS
    # ------------------------------------------------------------

    latest_point = cyclone["track"][-1]

    cyclone_latitude = float(
        latest_point.get("latitude", latitude)
    )

    cyclone_longitude = float(
        latest_point.get("longitude", longitude)
    )

    current_wind = float(
        latest_point.get("wind_kmph", 0)
    )

    wind_hazard = calculate_wind_hazard(
        cyclone_latitude,
        cyclone_longitude,
        current_wind,
        latitude,
        longitude,
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        current_wind,
        distance_from_coast_km,
        elevation_m,
    )

    flood_hazard = calculate_flood_hazard(
        rainfall_hazard,
        surge_hazard,
        elevation_m,
    )

    combined_hazard = calculate_combined_hazard(
        wind_hazard,
        rainfall_hazard,
        surge_hazard,
        flood_hazard,
    )

    current_hazards = {
        "wind": float(wind_hazard),
        "rainfall": float(rainfall_hazard),
        "storm_surge": float(surge_hazard),
        "flood": float(flood_hazard),
    }

    # ------------------------------------------------------------
    # VULNERABILITY
    # ------------------------------------------------------------

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
            float(
                location_context.get(
                    "healthcare_access",
                    0
                )
            )
        )
    )

    combined_vulnerability = calculate_vulnerability(
        population_vulnerability,
        infrastructure_vulnerability,
        agriculture_vulnerability,
        healthcare_vulnerability,
    )

    # ------------------------------------------------------------
    # EXPOSURE
    # ------------------------------------------------------------

    exposure = calculate_exposure(
        population_density=population_density,
        infrastructure_density=infrastructure_density,
        agriculture_percentage=agriculture_percentage,
    )

    # ------------------------------------------------------------
    # CURRENT RISK
    # ------------------------------------------------------------

    current_risk = calculate_risk_score(
        hazard=combined_hazard,
        exposure=exposure,
        vulnerability=combined_vulnerability,
    )

    # ------------------------------------------------------------
    # TRACK FORECAST
    # ------------------------------------------------------------

    track_forecast = calculate_track_risk_forecast(
        track=cyclone["track"],
        target_latitude=latitude,
        target_longitude=longitude,
        rainfall_mm=rainfall_mm,
        distance_from_coast_km=distance_from_coast_km,
        elevation_m=elevation_m,
        exposure=exposure,
        vulnerability=combined_vulnerability,
    )

    timeline = track_forecast.get(
        "timeline",
        []
    )

    # ------------------------------------------------------------
    # BUILD FUTURE FORECAST
    # ------------------------------------------------------------

    forecast_risks = []
    forecast_hazards = []

    for point in timeline:

        if point.get("forecast_type") != "projected":
            continue

        hours_ahead = point.get(
            "hours_ahead",
            0
        )

        risk_data = point.get(
            "risk",
            {}
        )

        hazards = point.get(
            "hazards",
            {}
        )

        forecast_risks.append({
            "hours_ahead": hours_ahead,
            "risk_score": float(
                risk_data.get("score", 0)
            ),
        })

        forecast_hazards.append({
            "hours_ahead": hours_ahead,
            "hazards": {
                "wind": float(
                    hazards.get("wind", 0)
                ),
                "rainfall": float(
                    hazards.get("rainfall", 0)
                ),
                "storm_surge": float(
                    hazards.get("storm_surge", 0)
                ),
                "flood": float(
                    hazards.get("flood", 0)
                ),
            },
        })

    # ------------------------------------------------------------
    # SAME INPUT FORMAT AS AUTOMATED MONITOR
    # ------------------------------------------------------------

    population_data = {
        "population_density": population_density
    }

    infrastructure_exposure = {
        "exposure": {
            "infrastructure_exposure_score": max(
                0.0,
                min(
                    1.0,
                    infrastructure_density
                )
            )
        }
    }

    # ------------------------------------------------------------
    # REAL EARLY-WARNING ENGINE
    # ------------------------------------------------------------

    trigger = evaluate_early_warning_trigger(
        current_risk=current_risk,
        forecast_risks=forecast_risks,
        current_hazards=current_hazards,
        forecast_hazards=forecast_hazards,
        population_data=population_data,
        infrastructure_exposure=infrastructure_exposure,
    )

    return {
        "success": True,

        "cyclone": {
            "id": cyclone.get("id"),
            "name": cyclone.get(
                "name",
                cyclone_id
            ),
        },

        "target": {
            "latitude": latitude,
            "longitude": longitude,
        },

        "warning": {
            "trigger": trigger.get(
                "trigger"
            ),
            "warning_level": trigger.get(
                "warning_level"
            ),
            "priority": trigger.get(
                "priority"
            ),
            "current_risk": trigger.get(
                "current_risk"
            ),
            "current_level": trigger.get(
                "current_level"
            ),
            "projected_risk": trigger.get(
                "projected_risk"
            ),
            "projected_level": trigger.get(
                "projected_level"
            ),
            "lead_time_hours": trigger.get(
                "lead_time_hours"
            ),
        },

        "hazards": current_hazards,

        "risk_forecast": forecast_risks,

        "hazard_forecast": forecast_hazards,

        "exposure": {
            "population_score": trigger.get(
                "population_exposure_score"
            ),
            "infrastructure_score": trigger.get(
                "infrastructure_exposure_score"
            ),
        },

        "reasons": trigger.get(
            "reasons",
            []
        ),

        "trigger_details": {
            "risk_escalation": trigger.get(
                "risk_escalation"
            ),
            "hazard_escalation": trigger.get(
                "hazard_escalation"
            ),
        },
    }

@router.get("/{cyclone_id}/advisory/{hours}")
def get_authority_advisory(
    cyclone_id: str,
    hours: int,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
):
    """Generate an authority advisory for a selected forecast hour."""

    allowed_hours = [6, 12, 18, 24, 30, 36]

    if hours not in allowed_hours:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported forecast hour",
                "allowed_hours": allowed_hours,
            },
        )

    cyclone = get_cyclone_by_id(cyclone_id)

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found",
        )

    # ------------------------------------------------------------
    # LOCATION CONTEXT
    # ------------------------------------------------------------

    location_context = get_location_context(
        latitude,
        longitude,
    )

    rainfall_mm = float(
        location_context.get("rainfall_mm", 0)
    )
    distance_from_coast_km = float(
        location_context.get("distance_from_coast_km", 0)
    )
    elevation_m = float(
        location_context.get("elevation_m", 0)
    )
    population_density = float(
        location_context.get("population_density", 0)
    )
    infrastructure_density = float(
        location_context.get("infrastructure_density", 0)
    )
    agriculture_percentage = float(
        location_context.get("agriculture_percentage", 0)
    )
    healthcare_access = float(
        location_context.get("healthcare_access", 0)
    )
    healthcare_data_status = location_context.get(
        "healthcare_data_status",
        "unknown",
    )

    # ------------------------------------------------------------
    # CURRENT CYCLONE / HAZARDS
    # ------------------------------------------------------------

    latest_point = cyclone["track"][-1]

    cyclone_latitude = float(
        latest_point.get("latitude", latitude)
    )
    cyclone_longitude = float(
        latest_point.get("longitude", longitude)
    )
    current_wind = float(
        latest_point.get("wind_kmph", 0)
    )

    wind_hazard = calculate_wind_hazard(
        cyclone_latitude,
        cyclone_longitude,
        current_wind,
        latitude,
        longitude,
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        current_wind,
        distance_from_coast_km,
        elevation_m,
    )

    flood_hazard = calculate_flood_hazard(
        rainfall_hazard,
        surge_hazard,
        elevation_m,
    )

    combined_hazard = calculate_combined_hazard(
        wind_hazard,
        rainfall_hazard,
        surge_hazard,
        flood_hazard,
    )

    current_hazards = {
        "wind": float(wind_hazard),
        "rainfall": float(rainfall_hazard),
        "storm_surge": float(surge_hazard),
        "flood": float(flood_hazard),
    }

    # ------------------------------------------------------------
    # VULNERABILITY
    # ------------------------------------------------------------

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
            healthcare_data_status,
        )
    )

    combined_vulnerability = calculate_vulnerability(
        population_vulnerability,
        infrastructure_vulnerability,
        agriculture_vulnerability,
        healthcare_vulnerability,
    )

    # ------------------------------------------------------------
    # EXPOSURE + CURRENT RISK
    # ------------------------------------------------------------

    exposure = calculate_exposure(
        population_density=population_density,
        infrastructure_density=infrastructure_density,
        agriculture_percentage=agriculture_percentage,
    )

    current_risk = calculate_risk_score(
        hazard=combined_hazard,
        exposure=exposure,
        vulnerability=combined_vulnerability,
    )

    # ------------------------------------------------------------
    # TRACK FORECAST
    # ------------------------------------------------------------

    forecast = calculate_track_risk_forecast(
        track=cyclone["track"],
        target_latitude=latitude,
        target_longitude=longitude,
        rainfall_mm=rainfall_mm,
        distance_from_coast_km=distance_from_coast_km,
        elevation_m=elevation_m,
        exposure=exposure,
        vulnerability=combined_vulnerability,
    )

    timeline = forecast.get("timeline", [])

    if not timeline:
        raise HTTPException(
            status_code=500,
            detail="No forecast timeline available",
        )

    point = next(
        (
            item
            for item in timeline
            if item.get("forecast_type") == "projected"
            and item.get("hours_ahead") == hours
        ),
        None,
    )

    if point is None:
        raise HTTPException(
            status_code=404,
            detail=f"No projected forecast available for +{hours} hours",
        )

    # ------------------------------------------------------------
    # BUILD FUTURE RISK / HAZARD ARRAYS
    # ------------------------------------------------------------

    forecast_risks = []
    forecast_hazards = []

    for forecast_point in timeline:
        if forecast_point.get("forecast_type") != "projected":
            continue

        hours_ahead = forecast_point.get("hours_ahead", 0)

        risk_data = forecast_point.get("risk", {})
        future_hazards = forecast_point.get("hazards", {})

        forecast_risks.append({
            "hours_ahead": hours_ahead,
            "risk_score": float(
                risk_data.get(
                    "score",
                    forecast_point.get("risk_score", 0),
                )
            ),
        })

        forecast_hazards.append({
            "hours_ahead": hours_ahead,
            "hazards": {
                "wind": float(
                    future_hazards.get("wind", 0)
                ),
                "rainfall": float(
                    future_hazards.get("rainfall", 0)
                ),
                "storm_surge": float(
                    future_hazards.get("storm_surge", 0)
                ),
                "flood": float(
                    future_hazards.get("flood", 0)
                ),
            },
        })

    # ------------------------------------------------------------
    # EARLY-WARNING ENGINE INPUT
    # ------------------------------------------------------------

    population_data = {
        "population_density": population_density,
    }

    infrastructure_exposure = {
        "exposure": {
            "infrastructure_exposure_score": max(
                0.0,
                min(
                    1.0,
                    infrastructure_density / 100.0,
                ),
            ),
        },
    }

    trigger = evaluate_early_warning_trigger(
        current_risk=current_risk,
        forecast_risks=forecast_risks,
        current_hazards=current_hazards,
        forecast_hazards=forecast_hazards,
        population_data=population_data,
        infrastructure_exposure=infrastructure_exposure,
    )

    # ------------------------------------------------------------
    # REQUESTED FORECAST POINT
    # ------------------------------------------------------------

    point_risk = point.get("risk", {})

    projected_risk = float(
        point_risk.get(
            "score",
            point.get("risk_score", 0),
        )
    )

    hazards = point.get("hazards", {})

    projected_hazards = {
        "wind": float(hazards.get("wind", 0)),
        "rainfall": float(hazards.get("rainfall", 0)),
        "storm_surge": float(
            hazards.get("storm_surge", 0)
        ),
        "flood": float(hazards.get("flood", 0)),
    }

    current_level = trigger.get(
        "current_level",
        classify_risk(current_risk),
    )

    projected_level = trigger.get(
        "projected_level",
        classify_risk(projected_risk),
    )

    trigger_reasons = trigger.get("reasons", [])

    if not trigger_reasons:
        trigger_reasons = [
            f"Forecast risk at +{hours} hours is "
            f"{projected_level}."
        ]

    population_score = trigger.get(
        "population_exposure_score",
        min(max(population_density / 100.0, 0.0), 1.0),
    )

    infrastructure_score = trigger.get(
        "infrastructure_exposure_score",
        infrastructure_exposure["exposure"][
            "infrastructure_exposure_score"
        ],
    )

    location_name = "Puri"

    # ------------------------------------------------------------
    # AUTHORITY GEMINI / FALLBACK ADVISORY
    # ------------------------------------------------------------

    advisory_result = generate_authority_advisory(
        cyclone_name=cyclone.get(
            "name",
            "Cyclone",
        ),
        location_name=location_name,
        authority_type="DISTRICT_DISASTER_MANAGEMENT",
        current_risk=current_risk,
        current_level=current_level,
        projected_risk=projected_risk,
        projected_level=projected_level,
        lead_time_hours=hours,
        hazards=projected_hazards,
        population_score=population_score,
        infrastructure_score=infrastructure_score,
        trigger_reasons=trigger_reasons,
    )

    return {
        "success": True,
        "cyclone": {
            "id": cyclone.get("id"),
            "name": cyclone.get(
                "name",
                cyclone_id,
            ),
        },
        "target": {
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name,
        },
        "forecast": {
            "hours_ahead": hours,
            "timestamp": point.get("timestamp"),
            "forecast_type": point.get("forecast_type"),
            "wind_kmph": point.get("wind_kmph"),
            "pressure_hpa": point.get("pressure_hpa"),
            "distance_to_location_km": point.get(
                "distance_to_location_km"
            ),
        },
        "warning": {
            "trigger": trigger.get("trigger"),
            "warning_level": trigger.get(
                "warning_level",
                projected_level,
            ),
            "current_level": current_level,
            "projected_level": projected_level,
            "current_risk": round(
                float(current_risk),
                4,
            ),
            "projected_risk": round(
                float(projected_risk),
                4,
            ),
            "current_percentage": round(
                float(current_risk) * 100,
                2,
            ),
            "projected_percentage": round(
                float(projected_risk) * 100,
                2,
            ),
            "lead_time_hours": hours,
        },
        "hazards": projected_hazards,
        "exposure": {
            "population_score": round(
                float(population_score),
                3,
            ),
            "infrastructure_score": round(
                float(infrastructure_score),
                3,
            ),
        },
        "trigger_details": {
            "risk_escalation": trigger.get(
                "risk_escalation"
            ),
            "hazard_escalation": trigger.get(
                "hazard_escalation"
            ),
            "reasons": trigger_reasons,
        },
        "advisory": advisory_result,
    }



@router.post("/{cyclone_id}/dispatch")
def dispatch_cyclone_advisory(
    cyclone_id: str,
    hours: int = 36,
    latitude: float = 19.8135,
    longitude: float = 85.8312,
    force: bool = True,
):
    """
    Manually dispatch the authority advisory for a forecast horizon.

    By default this performs a direct dispatch. Set force=false to
    apply the persistent anti-spam dispatch-state rules first.
    """

    allowed_hours = [6, 12, 18, 24, 30, 36]

    if hours not in allowed_hours:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported forecast hour",
                "allowed_hours": allowed_hours,
            },
        )

    cyclone = get_cyclone_by_id(cyclone_id)

    if not cyclone:
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found",
        )

    # Reuse the exact advisory pipeline already exposed by
    # GET /api/cyclones/{cyclone_id}/advisory/{hours}.
    advisory_response = get_authority_advisory(
        cyclone_id=cyclone_id,
        hours=hours,
        latitude=latitude,
        longitude=longitude,
    )

    advisory_result = advisory_response.get("advisory", {})
    advisory = advisory_result.get(
        "advisory",
        advisory_result,
    )

    warning = advisory_response.get("warning", {})
    target = advisory_response.get("target", {})

    warning_level = str(
        warning.get(
            "warning_level",
            warning.get("projected_level", "WATCH"),
        )
    ).upper()

    projected_risk = float(
        warning.get("projected_risk", 0.0)
    )

    trigger_details = advisory_response.get(
        "trigger_details",
        {},
    )

    reasons = trigger_details.get("reasons", [])

    reason = (
        reasons[0]
        if reasons
        else f"Manual advisory dispatch for +{hours} hour forecast."
    )

    location_name = str(
        target.get("location_name", "Puri")
    )

    cyclone_name = cyclone.get(
        "name",
        "Cyclone",
    )

    dispatch_decision = None

    if not force:
        from app.services.dispatch_state import evaluate_dispatch

        dispatch_decision = evaluate_dispatch(
            cyclone_name=cyclone_name,
            location_name=location_name,
            warning_level=warning_level,
            risk_score=projected_risk,
            reason=reason,
        )

        if not dispatch_decision.get("should_dispatch"):
            return {
                "success": True,
                "dispatch_required": False,
                "message": "Dispatch suppressed by anti-spam state.",
                "cyclone": advisory_response.get("cyclone"),
                "target": target,
                "forecast": advisory_response.get("forecast"),
                "warning": warning,
                "advisory": advisory_result,
                "dispatch_decision": dispatch_decision,
                "dispatch": None,
                "dispatch_state": get_dispatch_state(
                    cyclone_name,
                    location_name,
                ),
            }

    priority = (
        "CRITICAL"
        if warning_level == "EMERGENCY"
        else "HIGH"
        if warning_level == "HIGH"
        else "MEDIUM"
    )

    authority_decisions = [
        {
            "authority_type": "DISTRICT_DISASTER_MANAGEMENT",
            "priority": priority,
            "reason": reason,
        },
        {
            "authority_type": "MUNICIPAL_AUTHORITY",
            "priority": priority,
            "reason": reason,
        },
        {
            "authority_type": "BLOCK_ADMINISTRATION",
            "priority": priority,
            "reason": reason,
        },
        {
            "authority_type": "LOCAL_EMERGENCY_SERVICES",
            "priority": priority,
            "reason": reason,
        },
    ]

    dispatch_result = dispatch_authority_advisory(
        cyclone_name=cyclone_name,
        location_name=location_name,
        district=location_name,
        warning_level=warning_level,
        advisory=advisory,
        authority_decisions=authority_decisions,
    )

    if dispatch_result.get("success"):
        state = record_dispatch(
            cyclone_name=cyclone_name,
            location_name=location_name,
            warning_level=warning_level,
            risk_score=projected_risk,
            reason=reason,
        )
    else:
        state = get_dispatch_state(
            cyclone_name,
            location_name,
        )

    return {
        "success": bool(dispatch_result.get("success")),
        "dispatch_required": True,
        "message": (
            "Authority advisory dispatched."
            if dispatch_result.get("success")
            else "Authority advisory dispatch attempted, but no channel succeeded."
        ),
        "cyclone": advisory_response.get("cyclone"),
        "target": target,
        "forecast": advisory_response.get("forecast"),
        "warning": warning,
        "advisory": advisory_result,
        "dispatch_decision": dispatch_decision,
        "dispatch": dispatch_result,
        "dispatch_state": state,
    }


@router.get("/{cyclone_id}/monitor")
async def monitor_control(
    cyclone_id: str,
    action: str = "status",
):
    if cyclone_id != "CY001":
        raise HTTPException(
            status_code=404,
            detail=f"Cyclone {cyclone_id} not found"
        )

    if action == "start":
        result = await start_monitor()

        return {
            "success": True,
            "action": "start",
            "monitor": result,
        }

    if action == "stop":
        result = stop_monitor()

        return {
            "success": True,
            "action": "stop",
            "monitor": result,
        }

    if action == "status":
        return {
            "success": True,
            "action": "status",
            "monitor": get_monitor_status(),
        }

    raise HTTPException(
        status_code=400,
        detail="Invalid action. Use start, stop, or status."
    )