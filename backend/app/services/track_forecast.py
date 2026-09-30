from datetime import datetime, timedelta

from app.services.hazard import (
    calculate_distance,
    calculate_wind_hazard,
    calculate_rainfall_hazard,
    calculate_surge_hazard,
    calculate_flood_hazard,
    calculate_combined_hazard,
)

from app.services.risk_engine import (
    calculate_risk_score,
    classify_risk,
)


FORECAST_HOURS = [6, 12, 18, 24, 30, 36]


def parse_timestamp(timestamp):
    try:
        return datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except Exception:
        return None


def _calculate_point(
    point,
    target_latitude,
    target_longitude,
    rainfall_hazard,
    distance_from_coast_km,
    elevation_m,
    exposure,
    vulnerability,
    hours_from_start,
    hours_ahead,
    forecast_type,
):
    latitude = point["latitude"]
    longitude = point["longitude"]
    wind_kmph = point["wind_kmph"]
    pressure_hpa = point["pressure_hpa"]

    distance_to_location = calculate_distance(
        latitude,
        longitude,
        target_latitude,
        target_longitude,
    )

    wind_hazard = calculate_wind_hazard(
        latitude,
        longitude,
        wind_kmph,
        target_latitude,
        target_longitude,
    )

    surge_hazard = calculate_surge_hazard(
        wind_kmph,
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

    risk_score = calculate_risk_score(
        hazard=combined_hazard,
        exposure=exposure,
        vulnerability=vulnerability,
    )

    return {
        "timestamp": point["timestamp"],

        "hours_from_start": hours_from_start,

        "hours_ahead": hours_ahead,

        "forecast_type": forecast_type,

        "cyclone_position": {
            "latitude": latitude,
            "longitude": longitude,
        },

        "distance_to_location_km": round(
            distance_to_location,
            2
        ),

        "wind_kmph": wind_kmph,

        "pressure_hpa": pressure_hpa,

        "hazards": {
            "wind": wind_hazard,
            "rainfall": rainfall_hazard,
            "storm_surge": surge_hazard,
            "flood": flood_hazard,
            "combined": combined_hazard,
        },

        "risk": {
            "score": risk_score,

            "percentage": round(
                risk_score * 100,
                2
            ),

            "level": classify_risk(
                risk_score
            ),
        },
    }

def calculate_track_risk_forecast(
    track,
    target_latitude,
    target_longitude,
    rainfall_mm,
    distance_from_coast_km,
    elevation_m,
    exposure,
    vulnerability,
):

    if not track:
        return {
            "timeline": [],
            "peak": None,
            "closest_approach": None,
        }

    rainfall_hazard = calculate_rainfall_hazard(
        rainfall_mm
    )

    timeline = []

    # ========================================================
    # OBSERVED TRACK
    # ========================================================

    first_time = None
    latest_observed_hours_from_start = 0

    for point in track:

        point_time = parse_timestamp(
            point["timestamp"]
        )

        if point_time is not None:

            if first_time is None:
                first_time = point_time

            hours_from_start = round(
                (
                    point_time - first_time
                ).total_seconds() / 3600,
                2
            )

            latest_observed_hours_from_start = (
                hours_from_start
            )

        else:

            # Fallback if an observed point has
            # no valid timestamp.
            hours_from_start = (
                latest_observed_hours_from_start
            )

        timeline.append(
            _calculate_point(
                point=point,

                target_latitude=
                    target_latitude,

                target_longitude=
                    target_longitude,

                rainfall_hazard=
                    rainfall_hazard,

                distance_from_coast_km=
                    distance_from_coast_km,

                elevation_m=
                    elevation_m,

                exposure=
                    exposure,

                vulnerability=
                    vulnerability,

                hours_from_start=
                    hours_from_start,

                hours_ahead=0,

                forecast_type="observed",
            )
        )

    # ========================================================
    # FUTURE PROJECTION
    # ========================================================

    if len(track) >= 2:

        previous = track[-2]
        latest = track[-1]

        latest_time = parse_timestamp(
            latest["timestamp"]
        )

        # ----------------------------------------------------
        # Movement between last two observed points
        # ----------------------------------------------------

        lat_step = (
            latest["latitude"]
            - previous["latitude"]
        )

        lon_step = (
            latest["longitude"]
            - previous["longitude"]
        )

        wind_step = (
            latest["wind_kmph"]
            - previous["wind_kmph"]
        )

        pressure_step = (
            latest["pressure_hpa"]
            - previous["pressure_hpa"]
        )

        # ----------------------------------------------------
        # Generate future points
        # ----------------------------------------------------

        for hours in FORECAST_HOURS:

            steps = hours / 6.0

            projected_lat = (
                latest["latitude"]
                + lat_step * steps
            )

            projected_lon = (
                latest["longitude"]
                + lon_step * steps
            )

            # ------------------------------------------------
            # Damped intensity projection
            # ------------------------------------------------

            damping = 0.5

            projected_wind = (
                latest["wind_kmph"]
                + wind_step
                * steps
                * damping
            )

            projected_pressure = (
                latest["pressure_hpa"]
                + pressure_step
                * steps
                * damping
            )

            projected_wind = max(
                0,
                projected_wind
            )

            projected_pressure = max(
                850,
                projected_pressure
            )

            # ------------------------------------------------
            # Future timestamp
            # ------------------------------------------------

            if latest_time:

                projected_time = (
                    latest_time
                    + timedelta(hours=hours)
                ).isoformat()

            else:

                projected_time = (
                    f"forecast+{hours}h"
                )

            projected_point = {

                "timestamp":
                    projected_time,

                "latitude":
                    projected_lat,

                "longitude":
                    projected_lon,

                "wind_kmph":
                    projected_wind,

                "pressure_hpa":
                    projected_pressure,
            }

            # ------------------------------------------------
            # IMPORTANT
            #
            # Latest observed point is currently at
            # latest_observed_hours_from_start.
            #
            # Therefore:
            #
            # +6h  => 18 + 6  = 24h
            # +12h => 18 + 12 = 30h
            # +18h => 18 + 18 = 36h
            #
            # etc.
            # ------------------------------------------------

            projected_hours_from_start = (
                latest_observed_hours_from_start
                + hours
            )

            timeline.append(
                _calculate_point(
                    point=projected_point,

                    target_latitude=
                        target_latitude,

                    target_longitude=
                        target_longitude,

                    rainfall_hazard=
                        rainfall_hazard,

                    distance_from_coast_km=
                        distance_from_coast_km,

                    elevation_m=
                        elevation_m,

                    exposure=
                        exposure,

                    vulnerability=
                        vulnerability,

                    hours_from_start=
                        projected_hours_from_start,

                    hours_ahead=
                        hours,

                    forecast_type=
                        "projected",
                )
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    if not timeline:

        return {
            "timeline": [],
            "peak": None,
            "closest_approach": None,
        }

    # ========================================================
    # PEAK RISK
    # ========================================================

    peak = max(
        timeline,
        key=lambda item:
            item["risk"]["score"]
    )

    # ========================================================
    # CLOSEST APPROACH
    # ========================================================

    closest = min(
        timeline,
        key=lambda item:
            item["distance_to_location_km"]
    )

    return {

        "timeline":
            timeline,

        "peak": {

            "timestamp":
                peak["timestamp"],

            "risk_score":
                peak["risk"]["score"],

            "risk_percentage":
                peak["risk"]["percentage"],

            "risk_level":
                peak["risk"]["level"],

            "wind_kmph":
                peak["wind_kmph"],

            "pressure_hpa":
                peak["pressure_hpa"],

            "distance_to_location_km":
                peak[
                    "distance_to_location_km"
                ],

            "cyclone_latitude":
                peak[
                    "cyclone_position"
                ]["latitude"],

            "cyclone_longitude":
                peak[
                    "cyclone_position"
                ]["longitude"],
        },

        "closest_approach": {

            "timestamp":
                closest["timestamp"],

            "distance_to_location_km":
                closest[
                    "distance_to_location_km"
                ],

            "wind_kmph":
                closest["wind_kmph"],

            "pressure_hpa":
                closest["pressure_hpa"],

            "risk_percentage":
                closest[
                    "risk"
                ]["percentage"],

            "risk_level":
                closest[
                    "risk"
                ]["level"],
        },
    }