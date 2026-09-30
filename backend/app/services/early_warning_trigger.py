# ============================================================
# AUTOMATED EARLY-WARNING TRIGGER ENGINE
# ============================================================

from typing import Dict, Any, List


# ============================================================
# THRESHOLDS
# ============================================================

WATCH_THRESHOLD = 0.40
HIGH_THRESHOLD = 0.60
EMERGENCY_THRESHOLD = 0.80

# Hazard escalation thresholds
SIGNIFICANT_HAZARD_INCREASE = 0.05
MAJOR_HAZARD_INCREASE = 0.20


# ============================================================
# HELPERS
# ============================================================

def _score(value):
    """Safely normalize a value between 0 and 1."""

    try:
        value = float(value)

    except (
        TypeError,
        ValueError
    ):
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            value
        )
    )


def _level(score: float) -> str:
    score = _score(score)

    if score >= EMERGENCY_THRESHOLD:
        return "EMERGENCY"
    elif score >= HIGH_THRESHOLD:
        return "HIGH"
    elif score >= WATCH_THRESHOLD:
        return "WATCH"
    else:
        return "LOW"


def _threshold_for_level(level):
    """Return numeric threshold for a warning level."""

    if level == "EMERGENCY":
        return EMERGENCY_THRESHOLD

    if level == "HIGH":
        return HIGH_THRESHOLD

    if level == "WATCH":
        return WATCH_THRESHOLD

    return 0.0


# ============================================================
# FIND PROJECTED RISK
# ============================================================

def find_projected_escalation(
    current_risk,
    forecast_risks
):
    """
    Find future risk escalation.

    Two things are tracked:

    1. Threshold escalation
       LOW -> WATCH -> HIGH -> EMERGENCY

    2. Continuous future risk increase
       even when the next warning threshold has not
       yet been crossed.
    """

    current_risk = _score(
        current_risk
    )

    current_level = _level(
        current_risk
    )

    current_threshold = _threshold_for_level(
        current_level
    )

    forecast_risks = sorted(
        forecast_risks or [],
        key=lambda item: item.get(
            "hours_ahead",
            999999
        )
    )

    highest_future = None

    # --------------------------------------------------------
    # Examine future points
    # --------------------------------------------------------

    for forecast in forecast_risks:

        future_risk = _score(
            forecast.get(
                "risk_score",
                0
            )
        )

        hours_ahead = forecast.get(
            "hours_ahead"
        )

        future_level = _level(
            future_risk
        )

        future_threshold = _threshold_for_level(
            future_level
        )

        # ----------------------------------------------------
        # Keep highest projected risk
        # ----------------------------------------------------

        if (
            highest_future is None
            or future_risk >
                highest_future["risk_score"]
        ):

            highest_future = {
                "risk_score": future_risk,
                "level": future_level,
                "hours_ahead": hours_ahead,
            }

        # ----------------------------------------------------
        # Warning threshold escalation
        # ----------------------------------------------------

        if (
            future_level != current_level
            and future_threshold > current_threshold
        ):

            return {
                "escalation": True,

                "threshold_crossed": True,

                "current_level":
                    current_level,

                "projected_level":
                    future_level,

                "current_risk":
                    round(
                        current_risk,
                        3
                    ),

                "projected_risk":
                    round(
                        future_risk,
                        3
                    ),

                "hours_ahead":
                    hours_ahead,

                "reason": (
                    f"Projected risk is expected "
                    f"to reach {future_level} level."
                ),
            }

    # --------------------------------------------------------
    # No threshold crossed
    # --------------------------------------------------------

    if highest_future:

        future_risk = (
            highest_future["risk_score"]
        )

        increase = (
            future_risk -
            current_risk
        )

        return {
            "escalation": False,

            "threshold_crossed": False,

            "current_level":
                current_level,

            "projected_level":
                highest_future["level"],

            "current_risk":
                round(
                    current_risk,
                    3
                ),

            "projected_risk":
                round(
                    future_risk,
                    3
                ),

            "increase":
                round(
                    increase,
                    3
                ),

            "hours_ahead":
                highest_future[
                    "hours_ahead"
                ],

            "reason": (
                "Future risk is projected to "
                "increase but does not cross "
                "the next warning threshold."
            ),
        }

    # --------------------------------------------------------
    # No forecast
    # --------------------------------------------------------

    return {
        "escalation": False,

        "threshold_crossed": False,

        "current_level":
            current_level,

        "projected_level":
            current_level,

        "current_risk":
            round(
                current_risk,
                3
            ),

        "projected_risk":
            round(
                current_risk,
                3
            ),

        "increase": 0,

        "hours_ahead": None,

        "reason":
            "No future risk forecast available.",
    }


# ============================================================
# HAZARD ESCALATION
# ============================================================

def detect_hazard_escalation(
    current_hazards,
    forecast_hazards
):
    """
    Detect meaningful future increases in hazards.

    Supports:

        [
            {
                "hours_ahead": 6,
                "hazards": {
                    "wind": 0.72,
                    "rainfall": 0.65,
                    "storm_surge": 0.55,
                    "flood": 0.68
                }
            }
        ]

    A hazard increase >= 0.05 is considered meaningful.

    >= 0.20 is considered major.
    """

    current_hazards = (
        current_hazards or {}
    )

    forecast_hazards = (
        forecast_hazards or []
    )

    strongest = None

    normalized_forecasts = []

    # --------------------------------------------------------
    # Normalize dictionary format
    # --------------------------------------------------------

    if isinstance(
        forecast_hazards,
        dict
    ):

        timeline = (
            forecast_hazards.get(
                "timeline",
                []
            )
        )

        for point in timeline:

            if not isinstance(
                point,
                dict
            ):
                continue

            normalized_forecasts.append({

                "hours_ahead":
                    point.get(
                        "hours_ahead",
                        point.get(
                            "hours_from_start",
                            0
                        )
                    ),

                "hazards":
                    point.get(
                        "hazards",
                        {}
                    ),
            })

    # --------------------------------------------------------
    # Already normalized list
    # --------------------------------------------------------

    elif isinstance(
        forecast_hazards,
        list
    ):

        for forecast in forecast_hazards:

            if not isinstance(
                forecast,
                dict
            ):
                continue

            hazards = forecast.get(
                "hazards",
                {}
            )

            if not isinstance(
                hazards,
                dict
            ):
                continue

            normalized_forecasts.append({

                "hours_ahead":
                    forecast.get(
                        "hours_ahead",
                        0
                    ),

                "hazards":
                    hazards,
            })

    # --------------------------------------------------------
    # Compare current vs future
    # --------------------------------------------------------

    for forecast in normalized_forecasts:

        hours_ahead = forecast.get(
            "hours_ahead"
        )

        hazards = forecast.get(
            "hazards",
            {}
        )

        for (
            hazard_name,
            future_value
        ) in hazards.items():

            if hazard_name == "combined":
                continue

            current_value = _score(
                current_hazards.get(
                    hazard_name,
                    0
                )
            )

            future_value = _score(
                future_value
            )

            increase = (
                future_value -
                current_value
            )

            # ------------------------------------------------
            # Meaningful escalation
            # ------------------------------------------------

            if increase >= SIGNIFICANT_HAZARD_INCREASE:

                severity = "SIGNIFICANT"

                if (
                    increase >=
                    MAJOR_HAZARD_INCREASE
                ):
                    severity = "MAJOR"

                event = {

                    "hazard":
                        hazard_name,

                    "current_score":
                        round(
                            current_value,
                            3
                        ),

                    "projected_score":
                        round(
                            future_value,
                            3
                        ),

                    "increase":
                        round(
                            increase,
                            3
                        ),

                    "hours_ahead":
                        hours_ahead,

                    "severity":
                        severity,
                }

                # Keep strongest increase
                if (
                    strongest is None
                    or increase >
                        strongest["increase"]
                ):

                    strongest = event

    # --------------------------------------------------------
    # Escalation found
    # --------------------------------------------------------

    if strongest:

        return {

            "escalation":
                True,

            "hazard":
                strongest["hazard"],

            "current_score":
                strongest["current_score"],

            "projected_score":
                strongest["projected_score"],

            "increase":
                strongest["increase"],

            "hours_ahead":
                strongest["hours_ahead"],

            "severity":
                strongest["severity"],

            "reason": (
                f"{strongest['hazard']} hazard "
                f"is projected to increase "
                f"significantly."
            ),
        }

    # --------------------------------------------------------
    # No escalation
    # --------------------------------------------------------

    return {

        "escalation":
            False,

        "hazard":
            None,

        "current_score":
            0,

        "projected_score":
            0,

        "increase":
            0,

        "hours_ahead":
            None,

        "severity":
            None,

        "reason":
            "No significant hazard escalation detected.",
    }


# ============================================================
# MAIN TRIGGER
# ============================================================

def evaluate_early_warning_trigger(
    current_risk,
    forecast_risks=None,
    current_hazards=None,
    forecast_hazards=None,
    population_data=None,
    infrastructure_exposure=None
):
    """
    Main automated early-warning decision engine.
    """

    current_risk = _score(
        current_risk
    )

    current_level = _level(
        current_risk
    )

    # --------------------------------------------------------
    # Risk escalation
    # --------------------------------------------------------

    risk_escalation = (
        find_projected_escalation(
            current_risk=current_risk,
            forecast_risks=forecast_risks
        )
    )

    # --------------------------------------------------------
    # Hazard escalation
    # --------------------------------------------------------

    hazard_escalation = (
        detect_hazard_escalation(
            current_hazards=current_hazards,
            forecast_hazards=forecast_hazards
        )
    )

    # --------------------------------------------------------
    # Population exposure
    # --------------------------------------------------------

    population_score = 0.0

    if population_data:

        population_density = (
            population_data.get(
                "population_density",
                population_data.get(
                    "density",
                    0
                )
            )
        )

        try:

            population_density = float(
                population_density
            )

        except (
            TypeError,
            ValueError
        ):

            population_density = 0.0

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

    # --------------------------------------------------------
    # Infrastructure exposure
    # --------------------------------------------------------

    infrastructure_score = 0.0

    if infrastructure_exposure:

        exposure = (
            infrastructure_exposure.get(
                "exposure",
                {}
            )
        )

        infrastructure_score = _score(
            exposure.get(
                "infrastructure_exposure_score",
                0
            )
        )

    # --------------------------------------------------------
    # DETERMINE TRIGGER
    # --------------------------------------------------------

    trigger = False

    reasons = []

    warning_level = current_level

    # --------------------------------------------------------
    # Current HIGH / EMERGENCY
    # --------------------------------------------------------

    if current_risk >= HIGH_THRESHOLD:

        trigger = True

        reasons.append(
            "Current cyclone risk is at HIGH or EMERGENCY level."
        )

    # --------------------------------------------------------
    # Risk threshold escalation
    # --------------------------------------------------------

    if risk_escalation["escalation"]:

        trigger = True

        warning_level = (
            risk_escalation[
                "projected_level"
            ]
        )

        reasons.append(
            risk_escalation[
                "reason"
            ]
        )

    # --------------------------------------------------------
    # Hazard escalation
    # --------------------------------------------------------

    if hazard_escalation["escalation"]:

        trigger = True

        # Don't downgrade an existing warning level

        if warning_level == "LOW":

            warning_level = "WATCH"

        reasons.append(
            hazard_escalation[
                "reason"
            ]
        )

    # --------------------------------------------------------
    # High population exposure
    # --------------------------------------------------------

    if (
        population_score >= 0.8
        and current_risk >= WATCH_THRESHOLD
    ):

        trigger = True

        if warning_level == "LOW":

            warning_level = "WATCH"

        reasons.append(
            "High population exposure is present."
        )

    # --------------------------------------------------------
    # Significant infrastructure exposure
    # --------------------------------------------------------

    if (
        infrastructure_score >= 0.6
        and current_risk >= WATCH_THRESHOLD
    ):

        trigger = True

        if warning_level == "LOW":

            warning_level = "WATCH"

        reasons.append(
            "Significant infrastructure exposure is present."
        )

    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    if warning_level == "EMERGENCY":

        priority = "CRITICAL"

    elif warning_level == "HIGH":

        priority = "HIGH"

    elif warning_level == "WATCH":

        priority = "MEDIUM"

    else:

        priority = "LOW"

    # --------------------------------------------------------
    # LEAD TIME
    # --------------------------------------------------------

    lead_time_hours = None

    if risk_escalation["escalation"]:

        lead_time_hours = (
            risk_escalation[
                "hours_ahead"
            ]
        )

    elif hazard_escalation["escalation"]:

        lead_time_hours = (
            hazard_escalation[
                "hours_ahead"
            ]
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {

        "trigger":
            trigger,

        "warning_level":
            warning_level,

        "priority":
            priority,

        "current_risk":
            round(
                current_risk,
                3
            ),

        "current_level":
            current_level,

        "projected_risk":
            risk_escalation[
                "projected_risk"
            ],

        "projected_level":
            risk_escalation[
                "projected_level"
            ],

        "lead_time_hours":
            lead_time_hours,

        "risk_escalation":
            risk_escalation,

        "hazard_escalation":
            hazard_escalation,

        "population_exposure_score":
            round(
                population_score,
                3
            ),

        "infrastructure_exposure_score":
            round(
                infrastructure_score,
                3
            ),

        "reasons":
            reasons,

        "reason": (
            " ".join(reasons)
            if reasons
            else
            "No early-warning trigger detected."
        ),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 60)

    print(
        "AUTOMATED EARLY-WARNING TRIGGER TEST"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # DEMO FORECAST
    # --------------------------------------------------------

    current_risk = 0.48

    forecast_risks = [

        {
            "hours_ahead": 3,
            "risk_score": 0.52
        },

        {
            "hours_ahead": 6,
            "risk_score": 0.65
        },

        {
            "hours_ahead": 12,
            "risk_score": 0.82
        }
    ]

    current_hazards = {

        "wind": 0.45,

        "rainfall": 0.40,

        "storm_surge": 0.35,

        "flood": 0.38
    }

    forecast_hazards = [

        {
            "hours_ahead": 6,

            "hazards": {

                "wind": 0.72,

                "rainfall": 0.65,

                "storm_surge": 0.55,

                "flood": 0.68
            }
        }
    ]

    population_data = {

        "population_density":
            650
    }

    infrastructure_exposure = {

        "exposure": {

            "infrastructure_exposure_score":
                0.75
        }
    }

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    result = (
        evaluate_early_warning_trigger(
            current_risk=current_risk,
            forecast_risks=forecast_risks,
            current_hazards=current_hazards,
            forecast_hazards=forecast_hazards,
            population_data=population_data,
            infrastructure_exposure=
                infrastructure_exposure
        )
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()

    print(
        "TRIGGER:",
        result["trigger"]
    )

    print(
        "CURRENT RISK:",
        result["current_risk"]
    )

    print(
        "CURRENT LEVEL:",
        result["current_level"]
    )

    print(
        "PROJECTED RISK:",
        result["projected_risk"]
    )

    print(
        "PROJECTED LEVEL:",
        result["projected_level"]
    )

    print(
        "WARNING LEVEL:",
        result["warning_level"]
    )

    print(
        "PRIORITY:",
        result["priority"]
    )

    print(
        "LEAD TIME:",
        result["lead_time_hours"],
        "hours"
    )

    print()

    print("REASON:")

    for reason in result["reasons"]:

        print(
            "-",
            reason
        )

    print()

    print("=" * 60)