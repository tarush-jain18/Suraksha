# ============================================================
# EARLY WARNING / ALERT ENGINE
# ============================================================

from typing import Dict, List, Any


# ============================================================
# HELPERS
# ============================================================

def _score(value):
    """
    Safely convert a hazard/risk value into 0-1.
    """

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(0.0, min(1.0, value))


def _alert_level(score):
    """
    Convert normalized score into alert level.
    """

    score = _score(score)

    if score >= 0.80:
        return "EMERGENCY"

    if score >= 0.60:
        return "HIGH"

    if score >= 0.40:
        return "MODERATE"

    if score >= 0.20:
        return "WATCH"

    return "LOW"


def _make_alert(
    alert_id,
    category,
    score,
    title,
    message,
    action
):
    """
    Standard frontend-ready alert object.
    """

    score = round(_score(score), 3)

    return {
        "id": alert_id,
        "category": category,
        "level": _alert_level(score),
        "severity": score,
        "title": title,
        "message": message,
        "action": action
    }


# ============================================================
# CURRENT HAZARD ALERTS
# ============================================================

def generate_alerts(
    impact_risk,
    hazards
):
    """
    Generate alerts from current risk and hazard scores.

    Expected hazard keys:
        wind
        rainfall
        storm_surge
        flood
    """

    alerts = []

    impact_risk = _score(impact_risk)

    wind = _score(
        hazards.get("wind")
    )

    rainfall = _score(
        hazards.get("rainfall")
    )

    storm_surge = _score(
        hazards.get("storm_surge")
    )

    flood = _score(
        hazards.get("flood")
    )

    # --------------------------------------------------------
    # OVERALL RISK
    # --------------------------------------------------------

    if impact_risk >= 0.80:

        alerts.append(
            _make_alert(
                "risk_critical",
                "risk",
                impact_risk,
                "Critical Cyclone Risk",
                "Very high cyclone impact risk has been detected in the selected area.",
                "Follow official emergency instructions and move to a safe location if instructed."
            )
        )

    elif impact_risk >= 0.60:

        alerts.append(
            _make_alert(
                "risk_high",
                "risk",
                impact_risk,
                "High Cyclone Risk",
                "High cyclone impact risk has been detected in the selected area.",
                "Stay alert, secure property, and monitor official warnings."
            )
        )

    elif impact_risk >= 0.40:

        alerts.append(
            _make_alert(
                "risk_moderate",
                "risk",
                impact_risk,
                "Moderate Cyclone Risk",
                "Moderate cyclone impact risk is currently estimated for the selected area.",
                "Monitor updates and prepare basic emergency supplies."
            )
        )

    elif impact_risk >= 0.20:

        alerts.append(
            _make_alert(
                "risk_watch",
                "risk",
                impact_risk,
                "Cyclone Risk Watch",
                "Cyclone-related risk is present in the selected area.",
                "Continue monitoring official updates."
            )
        )

    # --------------------------------------------------------
    # WIND
    # --------------------------------------------------------

    if wind >= 0.80:

        alerts.append(
            _make_alert(
                "wind_emergency",
                "wind",
                wind,
                "Extreme Wind Hazard",
                "Very strong winds may create dangerous conditions.",
                "Stay indoors and avoid unnecessary travel."
            )
        )

    elif wind >= 0.60:

        alerts.append(
            _make_alert(
                "wind_high",
                "wind",
                wind,
                "High Wind Hazard",
                "Strong winds may affect people, roads and exposed structures.",
                "Secure loose objects and avoid exposed areas."
            )
        )

    elif wind >= 0.40:

        alerts.append(
            _make_alert(
                "wind_moderate",
                "wind",
                wind,
                "Wind Hazard",
                "Elevated wind conditions are expected.",
                "Exercise caution outdoors."
            )
        )

    # --------------------------------------------------------
    # RAINFALL
    # --------------------------------------------------------

    if rainfall >= 0.80:

        alerts.append(
            _make_alert(
                "rainfall_extreme",
                "rainfall",
                rainfall,
                "Extreme Rainfall Hazard",
                "Heavy rainfall may produce water accumulation and disruption.",
                "Avoid flooded areas and monitor local warnings."
            )
        )

    elif rainfall >= 0.60:

        alerts.append(
            _make_alert(
                "rainfall_high",
                "rainfall",
                rainfall,
                "Heavy Rainfall Alert",
                "Heavy rainfall may affect roads and low-lying areas.",
                "Avoid unnecessary travel through potentially flooded areas."
            )
        )

    elif rainfall >= 0.40:

        alerts.append(
            _make_alert(
                "rainfall_watch",
                "rainfall",
                rainfall,
                "Rainfall Watch",
                "Significant rainfall is possible in the affected area.",
                "Monitor rainfall and local updates."
            )
        )

    # --------------------------------------------------------
    # STORM SURGE
    # --------------------------------------------------------

    if storm_surge >= 0.80:

        alerts.append(
            _make_alert(
                "surge_extreme",
                "storm_surge",
                storm_surge,
                "Extreme Storm Surge Hazard",
                "Coastal areas may experience dangerous storm-surge conditions.",
                "Move away from exposed coastal areas if instructed by authorities."
            )
        )

    elif storm_surge >= 0.60:

        alerts.append(
            _make_alert(
                "surge_high",
                "storm_surge",
                storm_surge,
                "Storm Surge Alert",
                "Elevated storm-surge risk has been detected.",
                "Avoid exposed coastal and low-lying areas."
            )
        )

    elif storm_surge >= 0.40:

        alerts.append(
            _make_alert(
                "surge_watch",
                "storm_surge",
                storm_surge,
                "Storm Surge Watch",
                "Storm-surge conditions may affect coastal areas.",
                "Monitor official coastal warnings."
            )
        )

    # --------------------------------------------------------
    # FLOOD
    # --------------------------------------------------------

    if flood >= 0.80:

        alerts.append(
            _make_alert(
                "flood_extreme",
                "flood",
                flood,
                "Extreme Flood Risk",
                "Very high flood risk has been detected.",
                "Avoid flood-prone areas and follow evacuation instructions."
            )
        )

    elif flood >= 0.60:

        alerts.append(
            _make_alert(
                "flood_high",
                "flood",
                flood,
                "High Flood Risk",
                "Flooding may affect roads and low-lying areas.",
                "Avoid crossing flooded roads and streams."
            )
        )

    elif flood >= 0.40:

        alerts.append(
            _make_alert(
                "flood_watch",
                "flood",
                flood,
                "Flood Watch",
                "Flooding may occur in vulnerable areas.",
                "Monitor water levels and local warnings."
            )
        )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    alerts.sort(
        key=lambda alert: alert["severity"],
        reverse=True
    )

    return alerts


# ============================================================
# TRACK ALERTS
# ============================================================

def generate_track_alerts(
    cyclone_name,
    target_location,
    track_forecast
):
    """
    Generate alerts from track-risk forecast.
    """

    alerts = []

    if not track_forecast:
        return alerts

    # Support the different possible forecast formats.
    if isinstance(track_forecast, dict):

        score = (
            track_forecast.get("risk_score")
            or track_forecast.get("score")
            or track_forecast.get("risk")
            or 0
        )

        score = _score(score)

        if score >= 0.80:

            alerts.append(
                _make_alert(
                    "track_emergency",
                    "track",
                    score,
                    "Cyclone Track Alert",
                    f"{cyclone_name} shows high projected risk near {target_location}.",
                    "Monitor the projected track and follow official warnings."
                )
            )

        elif score >= 0.60:

            alerts.append(
                _make_alert(
                    "track_high",
                    "track",
                    score,
                    "Cyclone Track Watch",
                    f"{cyclone_name} may significantly affect {target_location}.",
                    "Continue monitoring the forecast track."
                )
            )

        elif score >= 0.40:

            alerts.append(
                _make_alert(
                    "track_watch",
                    "track",
                    score,
                    "Cyclone Track Monitoring",
                    f"{cyclone_name} has a developing risk near {target_location}.",
                    "Monitor future track updates."
                )
            )

    return alerts

def generate_population_alerts(population_data, risk_score):
    """
    Generate early-warning alerts based on population exposure.
    """

    if not population_data:
        return []

    population_density = population_data.get(
        "population_density",
        population_data.get("density", 0)
    )

    if population_density is None:
        population_density = 0

    population_density = float(population_density)

    # Normalize population density.
    # Adjust these thresholds later using Odisha-specific data.
    if population_density >= 1000:
        population_score = 1.0
    elif population_density >= 500:
        population_score = 0.8
    elif population_density >= 200:
        population_score = 0.6
    elif population_density >= 100:
        population_score = 0.4
    elif population_density > 0:
        population_score = 0.2
    else:
        population_score = 0.0

    # Combine population exposure with cyclone impact risk
    combined_score = (
        0.6 * float(risk_score) +
        0.4 * population_score
    )

    level = _alert_level(combined_score)

    if population_density >= 500:
        title = "High Population Exposure"
        message = (
            "A large population is located in an area exposed "
            "to the predicted cyclone impact."
        )
        action = (
            "Follow official evacuation instructions and move "
            "to designated safe shelters if advised."
        )

    elif population_density >= 200:
        title = "Significant Population Exposure"
        message = (
            "A significant population may be affected by the "
            "predicted cyclone conditions."
        )
        action = (
            "Stay alert for official warnings and keep emergency "
            "supplies and communication devices ready."
        )

    elif population_density > 0:
        title = "Population Exposure Alert"
        message = (
            "People in the selected area may be affected by "
            "the predicted cyclone conditions."
        )
        action = (
            "Monitor official warnings and avoid hazardous areas."
        )

    else:
        return []

    return [
        _make_alert(
            alert_id="population_exposure",
            category="population",
            score=combined_score,
            title=title,
            message=message,
            action=action,
        )
    ]

# ============================================================
# INFRASTRUCTURE ALERTS
# ============================================================

def generate_infrastructure_alerts(
    infrastructure_exposure
):
    """
    Generate alerts based on exposed infrastructure.
    """

    alerts = []

    if not infrastructure_exposure:
        return alerts

    summary = infrastructure_exposure.get(
        "summary",
        {}
    )

    total_assets = int(
        summary.get(
            "total_assets",
            infrastructure_exposure.get(
                "exposure",
                {}
            ).get(
                "asset_count",
                0
            )
        )
        or 0
    )

    roads = int(
        summary.get("roads", 0)
        or 0
    )

    bridges = int(
        summary.get("bridges", 0)
        or 0
    )

    schools = int(
        summary.get("schools", 0)
        or 0
    )

    healthcare = int(
        summary.get("healthcare", 0)
        or 0
    )

    critical = int(
        summary.get("critical_buildings", 0)
        or 0
    )

    # --------------------------------------------------------
    # GENERAL INFRASTRUCTURE
    # --------------------------------------------------------

    if total_assets > 0:

        severity = min(
            1.0,
            total_assets / 3500.0
        )

        alerts.append(
            _make_alert(
                "infrastructure_exposure",
                "infrastructure",
                severity,
                "Infrastructure Exposure Detected",
                f"{total_assets} infrastructure assets are mapped within the assessment area.",
                "Use the infrastructure map to identify exposed assets."
            )
        )

    # --------------------------------------------------------
    # BRIDGES
    # --------------------------------------------------------

    if bridges > 0:

        severity = min(
            1.0,
            bridges / 10.0
        )

        alerts.append(
            _make_alert(
                "bridge_exposure",
                "bridge",
                severity,
                "Bridge Exposure",
                f"{bridges} bridge assets are located within the assessment area.",
                "Check bridge and road conditions before travel."
            )
        )

    # --------------------------------------------------------
    # SCHOOLS
    # --------------------------------------------------------

    if schools > 0:

        severity = min(
            1.0,
            schools / 10.0
        )

        alerts.append(
            _make_alert(
                "school_exposure",
                "school",
                severity,
                "School Infrastructure Exposure",
                f"{schools} school assets are located within the assessment area.",
                "Local authorities should review school safety arrangements."
            )
        )

    # --------------------------------------------------------
    # HEALTHCARE
    # --------------------------------------------------------

    if healthcare > 0:

        severity = min(
            1.0,
            healthcare / 15.0
        )

        alerts.append(
            _make_alert(
                "healthcare_exposure",
                "healthcare",
                severity,
                "Healthcare Facility Exposure",
                f"{healthcare} healthcare facilities are mapped within the assessment area.",
                "Check accessibility and emergency preparedness."
            )
        )

    # --------------------------------------------------------
    # CRITICAL BUILDINGS
    # --------------------------------------------------------

    if critical > 0:

        severity = min(
            1.0,
            critical / 10.0
        )

        alerts.append(
            _make_alert(
                "critical_exposure",
                "critical_infrastructure",
                severity,
                "Critical Infrastructure Exposure",
                f"{critical} critical buildings are located within the assessment area.",
                "Review emergency access and continuity arrangements."
            )
        )

    # --------------------------------------------------------
    # ROADS
    # --------------------------------------------------------

    if roads > 0:

        severity = min(
            1.0,
            roads / 3500.0
        )

        alerts.append(
            _make_alert(
                "road_exposure",
                "roads",
                severity,
                "Road Network Exposure",
                f"{roads} road assets are mapped within the assessment area.",
                "Monitor road closures and avoid hazardous routes."
            )
        )

    alerts.sort(
        key=lambda alert: alert["severity"],
        reverse=True
    )

    return alerts


# ============================================================
# COMPLETE EARLY WARNING OUTPUT
# ============================================================
def generate_early_warnings(
    risk_result,
    infrastructure_exposure=None,
    population_data=None
):
    """
    Combine risk, hazard, track, infrastructure and population
    information into one frontend-ready early-warning response.
    """

    # --------------------------------------------------------
    # VALIDATE INPUT
    # --------------------------------------------------------

    if not risk_result:
        return {
            "success": False,
            "alert_count": 0,
            "highest_alert_level": "LOW",
            "alerts": [],
            "flash_messages": []
        }

    # --------------------------------------------------------
    # RISK + HAZARDS
    # --------------------------------------------------------

    hazards = risk_result.get(
        "hazards",
        {}
    )

    impact = risk_result.get(
        "impact",
        {}
    )

    risk_score = impact.get(
        "risk_score",
        0
    )

    # Make sure risk_score is numeric
    try:
        risk_score = float(risk_score)
    except (TypeError, ValueError):
        risk_score = 0.0

    # --------------------------------------------------------
    # 1. RISK + HAZARD ALERTS
    # --------------------------------------------------------

    alerts = generate_alerts(
        risk_score,
        hazards
    )

    # --------------------------------------------------------
    # 2. TRACK ALERTS
    # --------------------------------------------------------

    cyclone_name = (
        risk_result.get(
            "cyclone",
            {}
        ).get(
            "name",
            "Cyclone"
        )
    )

    location_name = (
        risk_result.get(
            "location",
            {}
        ).get(
            "name",
            "selected area"
        )
    )

    track_forecast = risk_result.get(
        "track_forecast",
        {}
    )

    track_alerts = generate_track_alerts(
        cyclone_name=cyclone_name,
        target_location=location_name,
        track_forecast=track_forecast
    )

    # --------------------------------------------------------
    # 3. INFRASTRUCTURE ALERTS
    # --------------------------------------------------------

    infrastructure_alerts = []

    if infrastructure_exposure:
        infrastructure_alerts = (
            generate_infrastructure_alerts(
                infrastructure_exposure
            )
        )

    # --------------------------------------------------------
    # 4. POPULATION EXPOSURE ALERTS
    # --------------------------------------------------------

    population_alerts = []

    if population_data:
        population_alerts = generate_population_alerts(
            population_data=population_data,
            risk_score=risk_score
        )

    # --------------------------------------------------------
    # 5. COMBINE ALL ALERTS
    # --------------------------------------------------------

    all_alerts = (
        alerts
        + track_alerts
        + infrastructure_alerts
        + population_alerts
    )

    # --------------------------------------------------------
    # 6. SORT BY SEVERITY
    # --------------------------------------------------------

    all_alerts.sort(
        key=lambda item: item.get(
            "severity",
            0
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # 7. FLASH MESSAGES
    # --------------------------------------------------------

    flash_messages = []

    for alert in all_alerts:

        flash_messages.append({
            "level": alert.get(
                "level",
                "LOW"
            ),

            "title": alert.get(
                "title",
                "Cyclone Alert"
            ),

            "message": alert.get(
                "message",
                ""
            ),

            "action": alert.get(
                "action",
                ""
            )
        })

    # --------------------------------------------------------
    # 8. HIGHEST ALERT LEVEL
    # --------------------------------------------------------

    highest_alert_level = (
        all_alerts[0].get(
            "level",
            "LOW"
        )
        if all_alerts
        else "LOW"
    )

    # --------------------------------------------------------
    # 9. FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "alert_count": len(
            all_alerts
        ),

        "highest_alert_level": (
            highest_alert_level
        ),

        "alerts": all_alerts,

        "flash_messages": flash_messages
    }

# ============================================================
# TEST
# ============================================================


if __name__ == "__main__":

    # --------------------------------------------------------
    # TEST HAZARDS
    # --------------------------------------------------------

    test_hazards = {
        "wind": 0.85,
        "rainfall": 0.72,
        "storm_surge": 0.65,
        "flood": 0.78
    }

    # --------------------------------------------------------
    # TEST RISK RESULT
    # --------------------------------------------------------

    test_risk_result = {
        "cyclone": {
            "name": "Demo Cyclone"
        },

        "location": {
            "name": "Puri"
        },

        "impact": {
            "risk_score": 0.82
        },

        "hazards": test_hazards,

        "track_forecast": {
            "risk_score": 0.70
        }
    }

    # --------------------------------------------------------
    # TEST INFRASTRUCTURE
    # --------------------------------------------------------

    test_infrastructure = {
        "summary": {
            "roads": 3506,
            "bridges": 4,
            "schools": 3,
            "healthcare": 10,
            "critical_buildings": 4,
            "total_assets": 3527
        },

        "exposure": {
            "asset_count": 3527
        }
    }

    # --------------------------------------------------------
    # TEST POPULATION
    # --------------------------------------------------------

    test_population = {
        "population_density": 650
    }

    # --------------------------------------------------------
    # GENERATE COMPLETE EARLY WARNINGS
    # --------------------------------------------------------

    result = generate_early_warnings(
        risk_result=test_risk_result,
        infrastructure_exposure=test_infrastructure,
        population_data=test_population
    )

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("EARLY WARNING TEST")
    print("=" * 60)

    print()
    print(
        "TOTAL ALERTS:",
        result["alert_count"]
    )

    print(
        "HIGHEST LEVEL:",
        result["highest_alert_level"]
    )

    print()

    for alert in result["alerts"]:

        print(
            f"[{alert['level']}] "
            f"{alert['title']}"
        )

        print(
            f"Category: {alert['category']}"
        )

        print(
            f"Severity: {alert['severity']}"
        )

        print(
            alert["message"]
        )

        print(
            "ACTION:",
            alert["action"]
        )

        print("-" * 60)