import json
import sys
from pathlib import Path

# ---------------------------------------------------------
# Make project root importable when running:
# python scripts/generate_dashboard_json.py
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# EXISTING BACKEND SERVICES
# ---------------------------------------------------------

from app.services.ingestion import get_cyclone_by_id

from app.services.data_sources.location_context import (
    get_location_context
)

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
    calculate_exposure,
    calculate_vulnerability,
    calculate_risk_score,
)

from app.services.track_forecast import (
    calculate_track_risk_forecast
)

from app.services.alert_engine import (
    generate_alerts,
    generate_track_alerts,
)

from app.services.historical import (
    get_historical_comparison,
)

from app.services.infrastructure_exposure import (
    calculate_infrastructure_exposure,
)

from app.services.impact_engine import (
    calculate_point_impact,
)

from app.services.early_warning_trigger import (
    evaluate_early_warning_trigger,
)

from app.services.authority_gemini_advisory import (
    generate_authority_advisory,
)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

CYCLONE_ID = "CY001"

TARGET_LATITUDE = 19.8135
TARGET_LONGITUDE = 85.8312

LOCATION_NAME = "Puri"
REGION = "Odisha"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "dashboard.json"


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def clean_for_json(value):
    """
    Convert values into JSON-safe Python objects.
    Handles numpy values and other non-standard objects.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(k): clean_for_json(v)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            clean_for_json(v)
            for v in value
        ]

    # numpy scalar support
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def generate_dashboard():

    print("\nGenerating frontend dashboard JSON...\n")

    # =====================================================
    # 1. LOAD CYCLONE
    # =====================================================

    cyclone = get_cyclone_by_id(CYCLONE_ID)

    if cyclone is None:
        raise RuntimeError(
            f"Cyclone {CYCLONE_ID} not found"
        )

    print(f"✓ Cyclone loaded: {cyclone.get('name', CYCLONE_ID)}")


    # =====================================================
    # 2. LOCATION CONTEXT
    # =====================================================

    location_context = get_location_context(
        latitude=TARGET_LATITUDE,
        longitude=TARGET_LONGITUDE
    )

    print("✓ Location context loaded")


    rainfall_mm = float(
        location_context.get("rainfall_mm", 0)
    )

    elevation_m = float(
        location_context.get("elevation_m", 0)
    )

    distance_from_coast_km = float(
        location_context.get(
            "distance_from_coast_km",
            0
        )
    )

    population_density = float(
        location_context.get(
            "population_density",
            0
        )
    )

    infrastructure_density = float(
        location_context.get(
            "infrastructure_density",
            0
        )
    )

    agriculture_percentage = float(
        location_context.get(
            "agriculture_percentage",
            0
        )
    )

    healthcare_access = location_context.get(
        "healthcare_access"
    )

    healthcare_data_status = location_context.get(
        "healthcare_data_status",
        "unknown"
    )


    # =====================================================
    # 3. CURRENT CYCLONE CONDITIONS
    # =====================================================

    track = cyclone.get("track", [])

    if not track:
        raise RuntimeError(
            f"Cyclone {CYCLONE_ID} has no track data"
        )

    latest_point = track[-1]

    cyclone_latitude = float(
        latest_point.get("latitude", 0)
    )

    cyclone_longitude = float(
        latest_point.get("longitude", 0)
    )

    current_wind = float(
        latest_point.get("wind_kmph", 0)
    )

    current_pressure = float(
        latest_point.get("pressure_hpa", 1013)
    )

    print("✓ Current cyclone conditions calculated")


    # =====================================================
    # 4. CURRENT HAZARDS
    # =====================================================

    wind_hazard = calculate_wind_hazard(
        cyclone_latitude,
        cyclone_longitude,
        current_wind,
        TARGET_LATITUDE,
        TARGET_LONGITUDE
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        current_wind,
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

    hazards = {
        "wind": wind_hazard,
        "rainfall": rainfall_hazard,
        "storm_surge": surge_hazard,
        "flood": flood_hazard,
        "combined": combined_hazard
    }

    print("✓ Hazards calculated")


    # =====================================================
    # 5. VULNERABILITY
    # =====================================================

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
        healthcare_vulnerability = 0
    else:
        healthcare_vulnerability = (
            calculate_healthcare_vulnerability(
                healthcare_access,
                healthcare_data_status
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

    vulnerability = {
        "population": population_vulnerability,
        "infrastructure": infrastructure_vulnerability,
        "agriculture": agriculture_vulnerability,
        "healthcare": healthcare_vulnerability,
        "combined": combined_vulnerability
    }

    print("✓ Vulnerability calculated")


    # =====================================================
    # 6. EXPOSURE
    # =====================================================

    exposure = calculate_exposure(
        population_density=population_density,
        infrastructure_density=infrastructure_density,
        agriculture_percentage=agriculture_percentage
    )

    exposure_data = {
        "population_density": population_density,
        "infrastructure_density": infrastructure_density,
        "agriculture_percentage": agriculture_percentage,
        "score": exposure
    }

    print("✓ Exposure calculated")


    # =====================================================
    # 7. CURRENT RISK
    # =====================================================

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

    risk = {
        "score": risk_score,
        "percentage": round(
            risk_score * 100,
            2
        ),
        "level": risk_level,
        "drivers": risk_drivers
    }

    print(
        f"✓ Current risk: "
        f"{round(risk_score * 100, 2)}% "
        f"({risk_level})"
    )


    # =====================================================
    # 8. TRACK FORECAST
    # =====================================================

    track_forecast = calculate_track_risk_forecast(
        track=track,
        target_latitude=TARGET_LATITUDE,
        target_longitude=TARGET_LONGITUDE,
        rainfall_mm=rainfall_mm,
        distance_from_coast_km=distance_from_coast_km,
        elevation_m=elevation_m,
        exposure=exposure,
        vulnerability=combined_vulnerability
    )

    timeline = track_forecast.get(
        "timeline",
        []
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

    print(
        f"✓ Forecast generated: "
        f"{len(observed)} observed, "
        f"{len(projected)} projected"
    )


    # =====================================================
    # 9. FORECAST TIMELINE FOR FRONTEND
    # =====================================================

    forecast_timeline = []

    for point in timeline:

        position = point.get(
            "cyclone_position",
            {}
        )

        point_risk = point.get(
            "risk",
            {}
        )

        point_hazards = point.get(
            "hazards",
            {}
        )

        point_risk_score = float(
            point_risk.get(
                "score",
                point.get("risk_score", 0)
            )
        )

        forecast_timeline.append({
            "hours_ahead": point.get(
                "hours_ahead",
                0
            ),

            "timestamp": point.get(
                "timestamp"
            ),

            "forecast_type": point.get(
                "forecast_type",
                "observed"
            ),

            "cyclone_position": {
                "latitude": position.get(
                    "latitude"
                ),
                "longitude": position.get(
                    "longitude"
                )
            },

            "wind_kmph": point.get(
                "wind_kmph"
            ),

            "pressure_hpa": point.get(
                "pressure_hpa"
            ),

            "distance_to_location_km": point.get(
                "distance_to_location_km"
            ),

            "risk": {
                "score": point_risk_score,
                "percentage": round(
                    point_risk_score * 100,
                    2
                ),
                "level": classify_risk(
                    point_risk_score
                )
            },

            "hazards": {
                "wind": point_hazards.get(
                    "wind",
                    0
                ),
                "rainfall": point_hazards.get(
                    "rainfall",
                    0
                ),
                "storm_surge": point_hazards.get(
                    "storm_surge",
                    0
                ),
                "flood": point_hazards.get(
                    "flood",
                    0
                )
            }
        })


    # =====================================================
    # 10. ALERTS
    # =====================================================

    alerts = generate_alerts(
        risk_score,
        hazards
    )

    track_alerts = generate_track_alerts(
        cyclone_name=cyclone.get(
            "name",
            CYCLONE_ID
        ),
        target_location=(
            f"{TARGET_LATITUDE}, "
            f"{TARGET_LONGITUDE}"
        ),
        track_forecast=track_forecast
    )

    print(
        f"✓ Alerts generated: "
        f"{len(alerts)} current"
    )


    # =====================================================
    # 11. HISTORICAL DATA
    # =====================================================

    historical = get_historical_comparison(
        current_wind_kmph=current_wind,
        current_pressure_hpa=current_pressure
    )

    print("✓ Historical comparison generated")


    # =====================================================
    # 12. INFRASTRUCTURE
    # =====================================================

    infrastructure = calculate_infrastructure_exposure(
        latitude=TARGET_LATITUDE,
        longitude=TARGET_LONGITUDE,
        radius_km=10
    )

    print("✓ Infrastructure exposure loaded")


    # =====================================================
    # 13. EARLY WARNING
    # =====================================================

    forecast_risks = []
    forecast_hazards = []

    for point in projected:

        point_risk = point.get(
            "risk",
            {}
        )

        point_hazards = point.get(
            "hazards",
            {}
        )

        forecast_risks.append({
            "hours_ahead": point.get(
                "hours_ahead",
                0
            ),

            "risk_score": float(
                point_risk.get(
                    "score",
                    point.get(
                        "risk_score",
                        0
                    )
                )
            )
        })

        forecast_hazards.append({
            "hours_ahead": point.get(
                "hours_ahead",
                0
            ),

            "hazards": {
                "wind": float(
                    point_hazards.get(
                        "wind",
                        0
                    )
                ),

                "rainfall": float(
                    point_hazards.get(
                        "rainfall",
                        0
                    )
                ),

                "storm_surge": float(
                    point_hazards.get(
                        "storm_surge",
                        0
                    )
                ),

                "flood": float(
                    point_hazards.get(
                        "flood",
                        0
                    )
                )
            }
        })


    population_data = {
        "population_density": population_density
    }

    infrastructure_exposure = {
        "exposure": {
            "infrastructure_exposure_score": max(
                0.0,
                min(
                    1.0,
                    infrastructure_density / 100.0
                )
            )
        }
    }

    warning_trigger = (
        evaluate_early_warning_trigger(
            current_risk=risk_score,
            forecast_risks=forecast_risks,
            current_hazards=hazards,
            forecast_hazards=forecast_hazards,
            population_data=population_data,
            infrastructure_exposure=(
                infrastructure_exposure
            )
        )
    )

    early_warning = {
        "trigger": warning_trigger.get(
            "trigger"
        ),

        "warning_level": warning_trigger.get(
            "warning_level"
        ),

        "priority": warning_trigger.get(
            "priority"
        ),

        "current_risk": warning_trigger.get(
            "current_risk"
        ),

        "current_level": warning_trigger.get(
            "current_level",
            risk_level
        ),

        "projected_risk": warning_trigger.get(
            "projected_risk"
        ),

        "projected_level": warning_trigger.get(
            "projected_level"
        ),

        "lead_time_hours": warning_trigger.get(
            "lead_time_hours"
        ),

        "risk_forecast": forecast_risks,

        "hazard_forecast": forecast_hazards,

        "reasons": warning_trigger.get(
            "reasons",
            []
        ),

        "trigger_details": {
            "risk_escalation": warning_trigger.get(
                "risk_escalation"
            ),

            "hazard_escalation": warning_trigger.get(
                "hazard_escalation"
            )
        }
    }

    print("✓ Early-warning result generated")


    # =====================================================
    # 14. MAP DATA
    # =====================================================

    observed_coordinates = []
    projected_coordinates = []
    map_points = []

    for point in timeline:

        position = point.get(
            "cyclone_position",
            {}
        )

        lat = position.get(
            "latitude"
        )

        lon = position.get(
            "longitude"
        )

        if lat is None or lon is None:
            continue

        coordinate = [
            lon,
            lat
        ]

        if point.get(
            "forecast_type"
        ) == "observed":

            observed_coordinates.append(
                coordinate
            )

        else:

            projected_coordinates.append(
                coordinate
            )

        map_points.append({
            "latitude": lat,
            "longitude": lon,

            "timestamp": point.get(
                "timestamp"
            ),

            "hours_from_start": point.get(
                "hours_from_start"
            ),

            "hours_ahead": point.get(
                "hours_ahead",
                0
            ),

            "forecast_type": point.get(
                "forecast_type",
                "observed"
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
                {}
            ),

            "risk": point.get(
                "risk",
                {}
            )
        })


    # Find peak risk point
    peak_point = None

    if timeline:

        peak_point = max(
            timeline,
            key=lambda point:
                point.get(
                    "risk",
                    {}
                ).get(
                    "score",
                    0
                )
        )

    peak_risk = (
        peak_point.get(
            "risk",
            {}
        )
        if peak_point
        else {}
    )


    map_data = {

        "center": {
            "latitude": TARGET_LATITUDE,
            "longitude": TARGET_LONGITUDE
        },

        "track": {

            "observed": {
                "type": "LineString",
                "coordinates": observed_coordinates
            },

            "projected": {
                "type": "LineString",
                "coordinates": projected_coordinates
            },

            "all_points": map_points
        },

        "target_marker": {
            "type": "Point",
            "coordinates": [
                TARGET_LONGITUDE,
                TARGET_LATITUDE
            ]
        },

        "peak_risk": peak_risk,

        "infrastructure": infrastructure,

        "alerts": alerts,

        "layers": {
            "cyclone_track": True,
            "projected_track": True,
            "risk": True,
            "hazards": True,
            "infrastructure": True,
            "alerts": True,
            "target": True
        }
    }


    # =====================================================
    # 15. ADVISORY
    # =====================================================

    advisory = {
        "available": False,
        "hours_ahead": None,
        "result": None
    }

    # Use first available projected forecast point
    if projected:

        advisory_point = projected[0]

        advisory_hours = advisory_point.get(
            "hours_ahead"
        )

        projected_risk_data = advisory_point.get(
            "risk",
            {}
        )

        projected_risk = float(
            projected_risk_data.get(
                "score",
                advisory_point.get(
                    "risk_score",
                    0
                )
            )
        )

        projected_level = classify_risk(
            projected_risk
        )

        projected_hazards = advisory_point.get(
            "hazards",
            {}
        )

        advisory_result = (
            generate_authority_advisory(
                cyclone_name=cyclone.get(
                    "name",
                    "Cyclone"
                ),

                location_name=LOCATION_NAME,

                authority_type=(
                    "DISTRICT_DISASTER_MANAGEMENT"
                ),

                current_risk=risk_score,

                current_level=risk_level,

                projected_risk=projected_risk,

                projected_level=projected_level,

                lead_time_hours=advisory_hours,

                hazards=projected_hazards,

                population_score=min(
                    max(
                        population_density / 100.0,
                        0.0
                    ),
                    1.0
                ),

                infrastructure_score=max(
                    0.0,
                    min(
                        1.0,
                        infrastructure_density / 100.0
                    )
                ),

                trigger_reasons=warning_trigger.get(
                    "reasons",
                    []
                )
            )
        )

        advisory = {
            "available": True,
            "hours_ahead": advisory_hours,
            "result": advisory_result
        }

        print("✓ Authority advisory generated")


    # =====================================================
    # 16. FINAL FRONTEND JSON
    # =====================================================

    dashboard = {

        "success": True,

        "cyclone": {
            "id": cyclone.get(
                "id",
                CYCLONE_ID
            ),

            "name": cyclone.get(
                "name",
                CYCLONE_ID
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

            "current_position": {
                "latitude": cyclone_latitude,
                "longitude": cyclone_longitude
            }
        },

        "location": {
            "name": LOCATION_NAME,
            "region": REGION,

            "latitude": TARGET_LATITUDE,
            "longitude": TARGET_LONGITUDE,

            "elevation_m": elevation_m,

            "distance_from_coast_km": (
                distance_from_coast_km
            )
        },

        "current_conditions": {
            "wind_kmph": current_wind,
            "pressure_hpa": current_pressure,
            "rainfall_mm": rainfall_mm
        },

        "risk": risk,

        "hazards": hazards,

        "vulnerability": vulnerability,

        "exposure": exposure_data,

        "forecast": {
            "observed": observed,
            "projected": projected,
            "peak": track_forecast.get(
                "peak",
                {}
            ),
            "closest_approach": (
                track_forecast.get(
                    "closest_approach",
                    {}
                )
            )
        },

        "forecast_timeline": forecast_timeline,

        "alerts": alerts,

        "track_alerts": track_alerts,

        "impact": {
            "risk_score": risk_score,
            "risk_percentage": round(
                risk_score * 100,
                2
            ),
            "risk_level": risk_level,
            "hazards": hazards,
            "cyclone": {
                "wind_kmph": current_wind,
                "pressure_hpa": current_pressure
            }
        },

        "infrastructure": infrastructure,

        "early_warning": early_warning,

        "advisory": advisory,

        "historical": historical,

        "map": map_data,

        "summary": {
            "risk_level": risk_level,
            "alert_count": len(alerts),
            "historical_summary": historical
        }
    }


    # =====================================================
    # 17. CLEAN + SAVE
    # =====================================================

    dashboard = clean_for_json(
        dashboard
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dashboard,
            file,
            indent=2,
            ensure_ascii=False
        )


    print("\n" + "=" * 60)
    print("DASHBOARD JSON GENERATED")
    print("=" * 60)

    print(
        f"File: {OUTPUT_FILE}"
    )

    print(
        f"Risk: "
        f"{dashboard['risk']['percentage']}%"
    )

    print(
        f"Level: "
        f"{dashboard['risk']['level']}"
    )

    print(
        f"Alerts: "
        f"{len(dashboard['alerts'])}"
    )

    print(
        f"Forecast points: "
        f"{len(dashboard['forecast_timeline'])}"
    )

    print("=" * 60)


    return dashboard


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    generate_dashboard()