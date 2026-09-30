from datetime import datetime, timezone
from pathlib import Path
import json


STATE_DIR = Path("data/processed/dispatch_state")
STATE_DIR.mkdir(parents=True, exist_ok=True)


LEVEL_PRIORITY = {
    "LOW": 0,
    "WATCH": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "EMERGENCY": 4,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _state_file(cyclone_name, location_name):
    safe_cyclone = cyclone_name.replace(" ", "_").lower()
    safe_location = location_name.replace(" ", "_").lower()

    return STATE_DIR / f"{safe_cyclone}_{safe_location}.json"


def _load_state(cyclone_name, location_name):
    path = _state_file(cyclone_name, location_name)

    if not path.exists():
        return {
            "cyclone_name": cyclone_name,
            "location_name": location_name,
            "last_warning_level": "LOW",
            "last_risk_score": 0.0,
            "last_dispatch_time": None,
            "last_reason": None,
            "dispatch_count": 0,
        }

    try:
        with open(path, "r") as f:
            return json.load(f)

    except Exception:
        return {
            "cyclone_name": cyclone_name,
            "location_name": location_name,
            "last_warning_level": "LOW",
            "last_risk_score": 0.0,
            "last_dispatch_time": None,
            "last_reason": None,
            "dispatch_count": 0,
        }


def _save_state(cyclone_name, location_name, state):
    path = _state_file(cyclone_name, location_name)

    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def evaluate_dispatch(
    cyclone_name,
    location_name,
    warning_level,
    risk_score,
    reason=None,
):
    """
    Decide whether a new advisory should be dispatched.

    Rules:

    WATCH -> HIGH          SEND
    HIGH -> EMERGENCY      SEND
    HIGH -> HIGH           DON'T SEND
    EMERGENCY -> EMERGENCY DON'T SEND

    Also sends when risk increases significantly
    even if the warning level remains the same.
    """

    warning_level = warning_level.upper()

    if warning_level not in LEVEL_PRIORITY:
        raise ValueError(
            f"Invalid warning level: {warning_level}"
        )

    risk_score = max(0.0, min(1.0, float(risk_score)))

    state = _load_state(
        cyclone_name,
        location_name
    )

    previous_level = state.get(
        "last_warning_level",
        "LOW"
    )

    previous_risk = float(
        state.get("last_risk_score", 0.0)
    )

    previous_priority = LEVEL_PRIORITY.get(
        previous_level,
        0
    )

    current_priority = LEVEL_PRIORITY.get(
        warning_level,
        0
    )

    risk_increase = risk_score - previous_risk

    should_dispatch = False
    dispatch_reason = "No significant escalation."

    # --------------------------------------------------
    # FIRST WARNING
    # --------------------------------------------------

    if previous_level == "LOW" and warning_level != "LOW":

        should_dispatch = True

        dispatch_reason = (
            f"Initial {warning_level} warning generated."
        )

    # --------------------------------------------------
    # LEVEL ESCALATION
    # --------------------------------------------------

    elif current_priority > previous_priority:

        should_dispatch = True

        dispatch_reason = (
            f"Risk escalated from "
            f"{previous_level} to {warning_level}."
        )

    # --------------------------------------------------
    # SAME LEVEL BUT SIGNIFICANT RISK INCREASE
    # --------------------------------------------------

    elif (
        current_priority == previous_priority
        and risk_increase >= 0.15
        and warning_level not in ["LOW"]
    ):

        should_dispatch = True

        dispatch_reason = (
            f"Risk increased significantly "
            f"from {previous_risk:.2f} "
            f"to {risk_score:.2f}."
        )

    # --------------------------------------------------
    # LOWER LEVEL
    # --------------------------------------------------

    elif current_priority < previous_priority:

        should_dispatch = False

        dispatch_reason = (
            f"Warning level decreased from "
            f"{previous_level} to {warning_level}; "
            f"no new escalation dispatch."
        )

    # --------------------------------------------------
    # UPDATE STATE
    # --------------------------------------------------

    result = {
        "should_dispatch": should_dispatch,
        "reason": dispatch_reason,
        "previous_level": previous_level,
        "current_level": warning_level,
        "previous_risk": round(previous_risk, 4),
        "current_risk": round(risk_score, 4),
        "risk_increase": round(risk_increase, 4),
        "last_dispatch_time": state.get(
            "last_dispatch_time"
        ),
    }

    # Update state only when a dispatch occurs.
    if should_dispatch:

        state["last_warning_level"] = warning_level
        state["last_risk_score"] = risk_score
        state["last_dispatch_time"] = _now()
        state["last_reason"] = (
            reason or dispatch_reason
        )
        state["dispatch_count"] = (
            state.get("dispatch_count", 0) + 1
        )

        _save_state(
            cyclone_name,
            location_name,
            state
        )

        result["dispatch_count"] = state[
            "dispatch_count"
        ]

    return result


def record_dispatch(
    cyclone_name,
    location_name,
    warning_level,
    risk_score,
    reason=None,
):
    """
    Explicitly record a successful dispatch.

    Useful when the actual SMS/email/webhook
    dispatch succeeds.
    """

    state = _load_state(
        cyclone_name,
        location_name
    )

    state["last_warning_level"] = warning_level.upper()
    state["last_risk_score"] = float(risk_score)
    state["last_dispatch_time"] = _now()
    state["last_reason"] = reason
    state["dispatch_count"] = (
        state.get("dispatch_count", 0) + 1
    )

    _save_state(
        cyclone_name,
        location_name,
        state
    )

    return state


def get_dispatch_state(
    cyclone_name,
    location_name
):
    """
    Get current dispatch state for a cyclone/location.
    """

    return _load_state(
        cyclone_name,
        location_name
    )


def reset_dispatch_state(
    cyclone_name,
    location_name
):
    """
    Reset dispatch state.
    Useful for testing a new cyclone.
    """

    path = _state_file(
        cyclone_name,
        location_name
    )

    if path.exists():
        path.unlink()

    return {
        "success": True,
        "message": "Dispatch state reset.",
        "cyclone_name": cyclone_name,
        "location_name": location_name,
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    cyclone = "Demo Cyclone"
    location = "Puri"

    print("=" * 60)
    print("DISPATCH STATE / ANTI-SPAM TEST")
    print("=" * 60)

    # Start clean
    reset_dispatch_state(
        cyclone,
        location
    )

    # --------------------------------------------------------
    # TEST 1
    # LOW -> WATCH
    # --------------------------------------------------------

    result = evaluate_dispatch(
        cyclone_name=cyclone,
        location_name=location,
        warning_level="WATCH",
        risk_score=0.45,
        reason="Cyclone approaching."
    )

    print("\nTEST 1: LOW -> WATCH")
    print(result)

    # --------------------------------------------------------
    # TEST 2
    # WATCH -> HIGH
    # --------------------------------------------------------

    result = evaluate_dispatch(
        cyclone_name=cyclone,
        location_name=location,
        warning_level="HIGH",
        risk_score=0.65,
        reason="Projected risk escalation."
    )

    print("\nTEST 2: WATCH -> HIGH")
    print(result)

    # --------------------------------------------------------
    # TEST 3
    # HIGH -> HIGH
    # Should NOT dispatch
    # --------------------------------------------------------

    result = evaluate_dispatch(
        cyclone_name=cyclone,
        location_name=location,
        warning_level="HIGH",
        risk_score=0.68,
        reason="Risk remains high."
    )

    print("\nTEST 3: HIGH -> HIGH")
    print(result)

    # --------------------------------------------------------
    # TEST 4
    # HIGH -> EMERGENCY
    # --------------------------------------------------------

    result = evaluate_dispatch(
        cyclone_name=cyclone,
        location_name=location,
        warning_level="EMERGENCY",
        risk_score=0.84,
        reason="Critical escalation."
    )

    print("\nTEST 4: HIGH -> EMERGENCY")
    print(result)

    # --------------------------------------------------------
    # TEST 5
    # EMERGENCY -> EMERGENCY
    # Should NOT dispatch
    # --------------------------------------------------------

    result = evaluate_dispatch(
        cyclone_name=cyclone,
        location_name=location,
        warning_level="EMERGENCY",
        risk_score=0.86,
        reason="Emergency conditions continue."
    )

    print("\nTEST 5: EMERGENCY -> EMERGENCY")
    print(result)

    # --------------------------------------------------------
    # FINAL STATE
    # --------------------------------------------------------

    print("\nFINAL STATE")
    print(
        get_dispatch_state(
            cyclone,
            location
        )
    )

    print("\n" + "=" * 60)