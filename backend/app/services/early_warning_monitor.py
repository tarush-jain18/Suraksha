import asyncio
import json
from datetime import datetime, timezone


from app.services.ingestion import (
    get_cyclone_by_id
)

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
)

from app.services.risk_engine import (
    classify_risk,
    calculate_exposure,
    calculate_vulnerability,
    calculate_risk_score,
)

from app.services.track_forecast import (
    calculate_track_risk_forecast,
)

from app.services.early_warning_pipeline import (
    run_early_warning_pipeline,
)


# ============================================================
# CONFIG
# ============================================================

MONITOR_INTERVAL_SECONDS = 300

# Demo cyclone
CYCLONE_ID = "CY001"

# Target location
TARGET_LATITUDE = 19.8135
TARGET_LONGITUDE = 85.8312

DISTRICT = "Puri"
LOCATION_NAME = "Puri"


# ============================================================
# MONITOR STATE
# ============================================================

monitor_state = {
    "running": False,
    "last_run": None,
    "run_count": 0,
    "last_result": None,
}


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


# ============================================================
# BUILD REAL CYCLONE DATA
# ============================================================

def get_current_cyclone_data():

    """
    Build the complete input required by the
    automated early-warning pipeline.

    Uses the real cyclone, hazard, vulnerability,
    exposure and track-forecast services.
    """

    # ========================================================
    # GET CYCLONE
    # ========================================================

    cyclone = get_cyclone_by_id(
        CYCLONE_ID
    )

    if cyclone is None:

        raise RuntimeError(
            f"Cyclone not found: {CYCLONE_ID}"
        )

    if not cyclone.get("track"):

        raise RuntimeError(
            f"Cyclone {CYCLONE_ID} has no track data."
        )


    # ========================================================
    # LOCATION CONTEXT
    # ========================================================

    location_context = get_location_context(
        TARGET_LATITUDE,
        TARGET_LONGITUDE,
    )

    rainfall_mm = safe_float(
        location_context.get(
            "rainfall_mm",
            0
        )
    )

    distance_from_coast_km = safe_float(
        location_context.get(
            "distance_from_coast_km",
            0
        )
    )

    elevation_m = safe_float(
        location_context.get(
            "elevation_m",
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


    # ========================================================
    # CURRENT CYCLONE POINT
    # ========================================================

    latest_point = cyclone["track"][-1]

    current_cyclone_latitude = safe_float(
        latest_point.get(
            "latitude",
            TARGET_LATITUDE
        )
    )

    current_cyclone_longitude = safe_float(
        latest_point.get(
            "longitude",
            TARGET_LONGITUDE
        )
    )

    current_wind_kmph = safe_float(
        latest_point.get(
            "wind_kmph",
            0
        )
    )


    # ========================================================
    # CURRENT HAZARDS
    # ========================================================

    wind_hazard = calculate_wind_hazard(
        current_cyclone_latitude,
        current_cyclone_longitude,
        current_wind_kmph,
        TARGET_LATITUDE,
        TARGET_LONGITUDE,
    )

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    surge_hazard = calculate_surge_hazard(
        current_wind_kmph,
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

        "wind":
            safe_float(wind_hazard),

        "rainfall":
            safe_float(rainfall_hazard),

        "storm_surge":
            safe_float(surge_hazard),

        "flood":
            safe_float(flood_hazard),
    }


    # ========================================================
    # VULNERABILITY
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
            healthcare_access
        )
    )

    combined_vulnerability = (
        calculate_vulnerability(
            population_vulnerability,
            infrastructure_vulnerability,
            agriculture_vulnerability,
            healthcare_vulnerability,
        )
    )


    # ========================================================
    # EXPOSURE
    # ========================================================

    exposure = calculate_exposure(

        population_density=
            population_density,

        infrastructure_density=
            infrastructure_density,

        agriculture_percentage=
            agriculture_percentage,
    )


    # ========================================================
    # CURRENT RISK
    # ========================================================

    impact_risk = calculate_risk_score(

        hazard=
            combined_hazard,

        exposure=
            exposure,

        vulnerability=
            combined_vulnerability,
    )

    risk_level = classify_risk(
        impact_risk
    )


    # ========================================================
    # TRACK RISK FORECAST
    # ========================================================

    track_forecast = (
        calculate_track_risk_forecast(

            track=
                cyclone["track"],

            target_latitude=
                TARGET_LATITUDE,

            target_longitude=
                TARGET_LONGITUDE,

            rainfall_mm=
                rainfall_mm,

            distance_from_coast_km=
                distance_from_coast_km,

            elevation_m=
                elevation_m,

            exposure=
                exposure,

            vulnerability=
                combined_vulnerability,
        )
    )


    # ========================================================
    # EXTRACT TIMELINE
    # ========================================================

    timeline = []

    if isinstance(
        track_forecast,
        dict
    ):

        timeline = track_forecast.get(
            "timeline",
            []
        )

    if not isinstance(
        timeline,
        list
    ):

        timeline = []


    # Keep only valid dictionary points
    timeline = [
        point
        for point in timeline
        if isinstance(point, dict)
    ]


    # Sort chronologically
    timeline.sort(
        key=lambda point: safe_float(
            point.get(
                "hours_from_start",
                0
            )
        )
    )


    # ========================================================
    # BUILD FORECAST RISK LIST
    # ========================================================

    forecast_risks = []

    forecast_hazards = []


    for point in timeline:

        hours_ahead = safe_float(
            point.get(
                "hours_from_start",
                0
            )
        )

        risk_data = point.get(
            "risk",
            {}
        )

        if not isinstance(
            risk_data,
            dict
        ):

            risk_data = {}


        future_risk = safe_float(
            risk_data.get(
                "score",
                0
            )
        )


        hazards = point.get(
            "hazards",
            {}
        )

        if not isinstance(
            hazards,
            dict
        ):

            hazards = {}


        forecast_risks.append({

            "hours_ahead":
                hours_ahead,

            "risk_score":
                future_risk,
        })


        forecast_hazards.append({

            "hours_ahead":
                hours_ahead,

            "hazards": {

                "wind":
                    safe_float(
                        hazards.get(
                            "wind",
                            0
                        )
                    ),

                "rainfall":
                    safe_float(
                        hazards.get(
                            "rainfall",
                            0
                        )
                    ),

                "storm_surge":
                    safe_float(
                        hazards.get(
                            "storm_surge",
                            0
                        )
                    ),

                "flood":
                    safe_float(
                        hazards.get(
                            "flood",
                            0
                        )
                    ),
            }
        })

    # ========================================================
    # BUILD TRUE FUTURE FORECAST
    #
    # The latest OBSERVED point is the current cyclone state.
    # PROJECTED points are the future forecast.
    # ========================================================

    future_forecast_risks = []

    future_forecast_hazards = []

    latest_observed_point = None

    # --------------------------------------------------------
    # Find the latest observed point
    # --------------------------------------------------------

    observed_points = [
        point
        for point in timeline
        if point.get("forecast_type") == "observed"
    ]

    if observed_points:
        latest_observed_point = max(
            observed_points,
            key=lambda point: safe_float(
                point.get(
                    "hours_from_start",
                    0
                )
            )
        )

    # --------------------------------------------------------
    # Use PROJECTED points only as future forecast
    # --------------------------------------------------------

    projected_points = [
        point
        for point in timeline
        if point.get("forecast_type") == "projected"
    ]

    # Sort projected points by forecast horizon

    projected_points.sort(
        key=lambda point: safe_float(
            point.get(
                "hours_ahead",
                0
            )
        )
    )

    # --------------------------------------------------------
    # Build forecast risk + hazard lists
    # --------------------------------------------------------

    for point in projected_points:

        hours_ahead = safe_float(
            point.get(
                "hours_ahead",
                0
            )
        )

        # Ignore invalid/non-future points

        if hours_ahead <= 0:
            continue

        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        risk_data = point.get(
            "risk",
            {}
        )

        if not isinstance(
            risk_data,
            dict
        ):
            risk_data = {}

        future_risk = safe_float(
            risk_data.get(
                "score",
                0
            )
        )

        future_forecast_risks.append({

            "hours_ahead":
                hours_ahead,

            "risk_score":
                future_risk,
        })

        # ----------------------------------------------------
        # Hazards
        # ----------------------------------------------------

        hazards = point.get(
            "hazards",
            {}
        )

        if not isinstance(
            hazards,
            dict
        ):
            hazards = {}

        future_forecast_hazards.append({

            "hours_ahead":
                hours_ahead,

            "hazards": {

                "wind":
                    safe_float(
                        hazards.get(
                            "wind",
                            0
                        )
                    ),

                "rainfall":
                    safe_float(
                        hazards.get(
                            "rainfall",
                            0
                        )
                    ),

                "storm_surge":
                    safe_float(
                        hazards.get(
                            "storm_surge",
                            0
                        )
                    ),

                "flood":
                    safe_float(
                        hazards.get(
                            "flood",
                            0
                        )
                    ),
            }
        })


    # ========================================================
    # NO OLD-TIMELINE FALLBACK
    #
    # IMPORTANT:
    # Never use historical/observed points as future
    # forecasts.
    # ========================================================

    if not future_forecast_risks:

        print(
            "\n[WARNING] No projected future risk points found."
        )

    if not future_forecast_hazards:

        print(
            "\n[WARNING] No projected future hazard points found."
        )

    # ========================================================
    # POPULATION
    # ========================================================

    population_data = {

        "population_density":
            population_density
    }


    # ========================================================
    # INFRASTRUCTURE
    # ========================================================

    infrastructure_exposure = {

        "exposure": {

            "infrastructure_exposure_score":
                max(
                    0.0,
                    min(
                        1.0,
                        infrastructure_density
                    )
                )
        }
    }


    # ========================================================
    # DEBUG SUMMARY
    # ========================================================

    print("\n")
    print(
        "========== EARLY WARNING DATA =========="
    )

    print(
        f"Current risk: "
        f"{impact_risk:.4f}"
    )

    print(
        f"Current risk level: "
        f"{risk_level}"
    )

    print(
        "\nCurrent hazards:"
    )

    print(
        json.dumps(
            current_hazards,
            indent=2
        )
    )

    print(
        "\nFuture risk forecast:"
    )

    print(
        json.dumps(
            future_forecast_risks,
            indent=2
        )
    )

    print(
        "\nFuture hazard forecast:"
    )

    print(
        json.dumps(
            future_forecast_hazards,
            indent=2
        )
    )

    print(
        "========================================\n"
    )


    # ========================================================
    # FINAL PIPELINE INPUT
    # ========================================================

    return {

        "cyclone_name":
            cyclone.get(
                "name",
                CYCLONE_ID
            ),

        "location_name":
            LOCATION_NAME,

        "district":
            DISTRICT,

        "current_risk":
            impact_risk,

        "forecast_risks":
            future_forecast_risks,

        "current_hazards":
            current_hazards,

        "forecast_hazards":
            future_forecast_hazards,

        "population_data":
            population_data,

        "infrastructure_exposure":
            infrastructure_exposure,
    }


# ============================================================
# RUN ONE MONITORING CYCLE
# ============================================================

async def run_monitor_cycle():

    print("\n")

    print("=" * 70)

    print(
        "REAL CYCLONE EARLY-WARNING MONITORING CYCLE"
    )

    print("=" * 70)


    timestamp = datetime.now(
        timezone.utc
    ).isoformat()


    print(
        f"Time: {timestamp}"
    )


    # ========================================================
    # GET REAL DATA
    # ========================================================

    try:

        data = get_current_cyclone_data()

    except Exception as exc:

        print(
            "\n[MONITOR DATA ERROR]"
        )

        print(
            str(exc)
        )

        result = {

            "success": False,

            "dispatch_required": True,

            "stage":
                "DATA_ERROR",

            "message":
                str(exc),
        }

        monitor_state["last_run"] = timestamp

        monitor_state["run_count"] += 1

        monitor_state["last_result"] = result

        return result


    # ========================================================
    # DISPLAY
    # ========================================================

    print(
        f"Cyclone: "
        f"{data['cyclone_name']}"
    )

    print(
        f"Location: "
        f"{data['location_name']}"
    )

    print(
        f"Current risk: "
        f"{data['current_risk']:.3f}"
    )


    # ========================================================
    # RUN EARLY WARNING PIPELINE
    # ========================================================

    try:

        result = run_early_warning_pipeline(
            **data
        )

    except Exception as exc:

        print(
            "\n[EARLY WARNING PIPELINE ERROR]"
        )

        print(
            str(exc)
        )

        result = {

            "success": False,

            "dispatch_required": True,

            "stage":
                "PIPELINE_ERROR",

            "message":
                str(exc),
        }


    # ========================================================
    # STORE MONITOR STATE
    # ========================================================

    monitor_state["last_run"] = timestamp

    monitor_state["run_count"] += 1

    monitor_state["last_result"] = result


    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\nMonitor result:"
    )

    print(
        f"Stage: "
        f"{result.get('stage')}"
    )

    print(
        f"Dispatch required: "
        f"{result.get('dispatch_required')}"
    )


    if result.get(
        "dispatch_required"
    ):

        print(
            "\n"
            "🚨 NEW EARLY WARNING DISPATCHED"
        )

    else:

        print(
            "No new dispatch required."
        )


    print(
        "=" * 70
    )


    return result


# ============================================================
# CONTINUOUS MONITOR
# ============================================================

async def start_monitor():

    if monitor_state["running"]:

        print(
            "Early-warning monitor "
            "is already running."
        )

        return


    monitor_state["running"] = True


    print("\n")

    print("=" * 70)

    print(
        "AUTOMATED REAL CYCLONE MONITOR STARTED"
    )

    print("=" * 70)

    print(
        f"Interval: "
        f"{MONITOR_INTERVAL_SECONDS} seconds"
    )


    try:

        while monitor_state["running"]:

            try:

                await run_monitor_cycle()

            except Exception as exc:

                print(
                    "\n[MONITOR ERROR]"
                )

                print(
                    str(exc)
                )


            if not monitor_state["running"]:

                break


            print(
                f"\nNext monitoring cycle in "
                f"{MONITOR_INTERVAL_SECONDS} seconds..."
            )


            await asyncio.sleep(
                MONITOR_INTERVAL_SECONDS
            )


    except asyncio.CancelledError:

        print(
            "\nEarly-warning monitor cancelled."
        )


    finally:

        monitor_state["running"] = False

        print(
            "Early-warning monitor stopped."
        )


# ============================================================
# STOP MONITOR
# ============================================================

def stop_monitor():

    monitor_state["running"] = False

    return {

        "success":
            True,

        "message":
            "Early-warning monitor "
            "stop requested.",
    }


# ============================================================
# STATUS
# ============================================================

def get_monitor_status():

    last_result = (
        monitor_state["last_result"]
    )


    return {

        "running":
            monitor_state["running"],

        "last_run":
            monitor_state["last_run"],

        "run_count":
            monitor_state["run_count"],

        "last_stage":
            (
                last_result.get(
                    "stage"
                )
                if last_result
                else None
            ),

        "last_dispatch_required":
            (
                last_result.get(
                    "dispatch_required"
                )
                if last_result
                else None
            ),
        "last_result":
            last_result,
    }



# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    result = asyncio.run(
        run_monitor_cycle()
    )


    print("\n")


    print(
        json.dumps(
            result,
            indent=2
        )
    )