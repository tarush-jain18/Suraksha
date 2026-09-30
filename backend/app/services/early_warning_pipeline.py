import json
import sys

from app.services.early_warning_trigger import (
    evaluate_early_warning_trigger,
)

from app.services.dispatch_state import (
    evaluate_dispatch,
    reset_dispatch_state,
)

from app.services.authority_priority import (
    evaluate_authority_priority,
)

from app.services.authority_gemini_advisory import (
    generate_authority_advisory,
)

from app.services.dispatch_engine import (
    dispatch_authority_advisory,
)


# ============================================================
# AUTOMATED EARLY-WARNING PIPELINE
# ============================================================

def run_early_warning_pipeline(
    cyclone_name,
    location_name,
    district,

    current_risk,
    forecast_risks,

    current_hazards,
    forecast_hazards,

    population_data,
    infrastructure_exposure,
):
    """
    Complete automated early-warning pipeline.

    IMPORTANT:
    This function NEVER resets dispatch state.

    It can therefore be called repeatedly by a scheduler,
    monitoring service, API endpoint, or background worker.

    Flow:

        Risk Forecast
             ↓
        Early Warning Trigger
             ↓
        Anti-Spam State
             ↓
        Authority Priority
             ↓
        Authority Advisory
             ↓
        Dispatch
             ↓
        Dispatch Log
    """

    # ========================================================
    # STEP 1
    # EARLY-WARNING TRIGGER
    # ========================================================

    trigger = evaluate_early_warning_trigger(
        current_risk=current_risk,
        forecast_risks=forecast_risks,
        current_hazards=current_hazards,
        forecast_hazards=forecast_hazards,
        population_data=population_data,
        infrastructure_exposure=infrastructure_exposure,
    )

    # --------------------------------------------------------
    # No trigger
    # --------------------------------------------------------

    if not trigger.get("trigger", False):

        return {
            "success": True,
            "dispatch_required": False,
            "stage": "TRIGGER_CHECK",
            "message": (
                "No early-warning dispatch required."
            ),
            "trigger": trigger,
        }

    # ========================================================
    # STEP 2
    # EXTRACT WARNING INFORMATION
    # ========================================================

    warning_level = trigger.get(
        "warning_level",
        trigger.get(
            "projected_level",
            "WATCH"
        )
    )

    projected_risk = trigger.get(
        "projected_risk",
        current_risk
    )

    lead_time_hours = trigger.get(
        "lead_time_hours"
    )

    reasons = trigger.get(
        "reasons",
        []
    )

    # ========================================================
    # STEP 3
    # ANTI-SPAM / DISPATCH STATE
    # ========================================================

    dispatch_decision = evaluate_dispatch(
        cyclone_name=cyclone_name,
        location_name=location_name,
        warning_level=warning_level,
        risk_score=projected_risk,
        reason=trigger.get("reason"),
    )

    # --------------------------------------------------------
    # Already dispatched
    # --------------------------------------------------------

    if not dispatch_decision.get(
        "should_dispatch",
        False
    ):

        return {
            "success": True,

            "dispatch_required": False,

            "stage": "ANTI_SPAM",

            "message": (
                "Warning already dispatched or "
                "no significant escalation."
            ),

            "trigger": trigger,

            "dispatch_decision":
                dispatch_decision,
        }

    # ========================================================
    # STEP 4
    # EXPOSURE SCORES
    # ========================================================

    population_score = trigger.get(
        "population_exposure_score",
        0.0
    )

    infrastructure_score = trigger.get(
        "infrastructure_exposure_score",
        0.0
    )

    # ========================================================
    # STEP 5
    # AUTHORITY PRIORITY
    # ========================================================

    authority_priority = evaluate_authority_priority(
        warning_level=warning_level,
        lead_time_hours=lead_time_hours,
        population_score=population_score,
        infrastructure_score=infrastructure_score,
    )

    authority_decisions = (
        authority_priority.get(
            "authorities",
            []
        )
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not authority_decisions:

        return {
            "success": False,

            "dispatch_required": False,

            "stage": "AUTHORITY_SELECTION",

            "message": (
                "Warning triggered but no authority "
                "targets were selected."
            ),

            "trigger": trigger,

            "dispatch_decision":
                dispatch_decision,

            "authority_priority":
                authority_priority,
        }

    # ========================================================
    # STEP 6
    # AUTHORITY ADVISORY
    # ========================================================

    # Generate one advisory using the highest-priority
    # authority type. The same structured advisory can
    # then be dispatched to all selected authorities.

    first_authority = authority_decisions[0]

    authority_type = first_authority.get(
        "authority_type",
        "MUNICIPAL_AUTHORITY"
    )

    # --------------------------------------------------------
    # Select forecast hazards
    # --------------------------------------------------------

    advisory_hazards = current_hazards

    if forecast_hazards:

        # Find the earliest forecast point associated
        # with the detected lead time.

        selected_forecast = None

        for forecast in forecast_hazards:

            if (
                lead_time_hours is not None
                and forecast.get("hours_ahead")
                == lead_time_hours
            ):
                selected_forecast = forecast
                break

        # If exact lead time isn't found, use first
        # forecast entry.

        if selected_forecast is None:
            selected_forecast = forecast_hazards[0]

        advisory_hazards = selected_forecast.get(
            "hazards",
            current_hazards
        )

    # ========================================================
    # STEP 7
    # GENERATE AUTHORITY ADVISORY
    # ========================================================

    advisory_result = generate_authority_advisory(

        cyclone_name=cyclone_name,

        location_name=location_name,

        authority_type=authority_type,

        current_risk=current_risk,

        current_level=trigger.get(
            "current_level",
            "WATCH"
        ),

        projected_risk=projected_risk,

        projected_level=warning_level,

        lead_time_hours=lead_time_hours,

        hazards=advisory_hazards,

        population_score=population_score,

        infrastructure_score=infrastructure_score,

        trigger_reasons=reasons,
    )

    advisory = advisory_result.get(
        "advisory"
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not advisory:

        return {
            "success": False,

            "dispatch_required": False,

            "stage": "ADVISORY_GENERATION",

            "message": (
                "Warning triggered but advisory "
                "generation failed."
            ),

            "trigger": trigger,

            "dispatch_decision":
                dispatch_decision,

            "authority_priority":
                authority_priority,

            "advisory":
                advisory_result,
        }

    # ========================================================
    # STEP 8
    # DISPATCH
    # ========================================================

    dispatch_result = dispatch_authority_advisory(

        cyclone_name=cyclone_name,

        location_name=location_name,

        district=district,

        warning_level=warning_level,

        advisory=advisory,

        authority_decisions=authority_decisions,
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "success": True,

        "dispatch_required": True,

        "stage": "DISPATCHED",

        "cyclone_name":
            cyclone_name,

        "location_name":
            location_name,

        "trigger":
            trigger,

        "dispatch_decision":
            dispatch_decision,

        "authority_priority":
            authority_priority,

        "advisory":
            advisory_result,

        "dispatch":
            dispatch_result,
    }


# ============================================================
# DEMO INPUT
# ============================================================

def get_demo_input():
    """
    Demo cyclone data used only for testing.
    """

    current_risk = 0.48

    forecast_risks = [
        {
            "hours_ahead": 3,
            "risk_score": 0.52,
        },
        {
            "hours_ahead": 6,
            "risk_score": 0.65,
        },
        {
            "hours_ahead": 12,
            "risk_score": 0.82,
        },
    ]

    current_hazards = {
        "wind": 0.45,
        "rainfall": 0.40,
        "storm_surge": 0.35,
        "flood": 0.38,
    }

    forecast_hazards = [
        {
            "hours_ahead": 6,

            "hazards": {
                "wind": 0.72,
                "rainfall": 0.65,
                "storm_surge": 0.55,
                "flood": 0.68,
            },
        }
    ]

    population_data = {
        "population_density": 650,
    }

    infrastructure_exposure = {
        "exposure": {
            "infrastructure_exposure_score": 0.75
        }
    }

    return {
        "cyclone_name":
            "Demo Cyclone",

        "location_name":
            "Puri",

        "district":
            "Puri",

        "current_risk":
            current_risk,

        "forecast_risks":
            forecast_risks,

        "current_hazards":
            current_hazards,

        "forecast_hazards":
            forecast_hazards,

        "population_data":
            population_data,

        "infrastructure_exposure":
            infrastructure_exposure,
    }


# ============================================================
# TEST RUNNER
# ============================================================

def run_demo():

    demo = get_demo_input()

    result = run_early_warning_pipeline(
        **demo
    )

    print("\n")
    print("=" * 70)
    print("FINAL PIPELINE RESULT")
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=2
        )
    )


# ============================================================
# RESET + TEST
# ============================================================

def reset_demo_state():

    result = reset_dispatch_state(
        "Demo Cyclone",
        "Puri",
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("FULL AUTOMATED EARLY-WARNING PIPELINE")
    print("=" * 70)

    # --------------------------------------------------------
    # --reset
    #
    # Explicitly starts a fresh test.
    #
    # Normal monitoring NEVER resets state.
    # --------------------------------------------------------

    if "--reset" in sys.argv:

        print("\nResetting Demo Cyclone dispatch state...\n")

        reset_demo_state()

    print("\nRunning pipeline...\n")

    run_demo()