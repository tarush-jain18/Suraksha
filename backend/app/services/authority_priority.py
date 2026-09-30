from typing import Optional


# ============================================================
# LEAD-TIME RULES
# ============================================================

LEAD_TIME_PRIORITY = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


def calculate_lead_time_priority(
    lead_time_hours: Optional[float]
):
    """
    Convert projected warning lead time into an urgency class.

    The earlier the warning needs to be acted upon,
    the higher the operational priority.
    """

    if lead_time_hours is None:
        return {
            "lead_time_hours": None,
            "lead_time_class": "UNKNOWN",
            "priority": "LOW",
            "reason": "Lead time is unavailable."
        }

    lead_time_hours = float(lead_time_hours)

    if lead_time_hours <= 3:
        lead_time_class = "IMMEDIATE"
        priority = "CRITICAL"

    elif lead_time_hours <= 6:
        lead_time_class = "SHORT"
        priority = "HIGH"

    elif lead_time_hours <= 12:
        lead_time_class = "EARLY"
        priority = "MEDIUM"

    else:
        lead_time_class = "ADVANCE"
        priority = "LOW"

    return {
        "lead_time_hours": round(lead_time_hours, 2),
        "lead_time_class": lead_time_class,
        "priority": priority,
        "reason": (
            f"Projected escalation is {lead_time_hours:.1f} "
            f"hours away."
        )
    }


# ============================================================
# AUTHORITY PRIORITY
# ============================================================

AUTHORITY_LEVELS = {
    "DISTRICT_DISASTER_MANAGEMENT": 4,
    "MUNICIPAL_AUTHORITY": 3,
    "BLOCK_ADMINISTRATION": 2,
    "LOCAL_EMERGENCY_SERVICES": 1,
}


def get_authority_priority(
    warning_level: str,
    lead_time_hours: Optional[float] = None,
    population_score: float = 0.0,
    infrastructure_score: float = 0.0,
):
    """
    Determine which authority groups should receive
    the warning and their operational priority.

    This does NOT send anything.
    It only decides dispatch priority.
    """

    warning_level = warning_level.upper()

    population_score = max(
        0.0,
        min(1.0, float(population_score))
    )

    infrastructure_score = max(
        0.0,
        min(1.0, float(infrastructure_score))
    )

    lead_time = calculate_lead_time_priority(
        lead_time_hours
    )

    authorities = []

    # --------------------------------------------------------
    # DISTRICT DISASTER MANAGEMENT
    # --------------------------------------------------------

    if warning_level in ["HIGH", "EMERGENCY"]:

        authorities.append({
            "authority_type":
                "DISTRICT_DISASTER_MANAGEMENT",
            "priority": "CRITICAL"
                if warning_level == "EMERGENCY"
                else "HIGH",
            "reason":
                "High-level cyclone risk requires "
                "district disaster coordination."
        })

    # --------------------------------------------------------
    # MUNICIPAL AUTHORITY
    # --------------------------------------------------------

    if warning_level in [
        "WATCH",
        "MODERATE",
        "HIGH",
        "EMERGENCY"
    ]:

        municipal_priority = "MEDIUM"

        if warning_level == "HIGH":
            municipal_priority = "HIGH"

        elif warning_level == "EMERGENCY":
            municipal_priority = "CRITICAL"

        authorities.append({
            "authority_type":
                "MUNICIPAL_AUTHORITY",
            "priority": municipal_priority,
            "reason":
                "Municipal authorities may need to "
                "prepare local response operations."
        })

    # --------------------------------------------------------
    # BLOCK ADMINISTRATION
    # --------------------------------------------------------

    if (
        population_score >= 0.6
        or warning_level in ["HIGH", "EMERGENCY"]
    ):

        authorities.append({
            "authority_type":
                "BLOCK_ADMINISTRATION",
            "priority":
                "HIGH"
                if population_score >= 0.8
                else "MEDIUM",
            "reason":
                "Population exposure requires "
                "local administrative coordination."
        })

    # --------------------------------------------------------
    # LOCAL EMERGENCY SERVICES
    # --------------------------------------------------------

    if (
        infrastructure_score >= 0.6
        or warning_level == "EMERGENCY"
    ):

        authorities.append({
            "authority_type":
                "LOCAL_EMERGENCY_SERVICES",
            "priority":
                "CRITICAL"
                if warning_level == "EMERGENCY"
                else "HIGH",
            "reason":
                "Infrastructure exposure may require "
                "local emergency response readiness."
        })

    # --------------------------------------------------------
    # LEAD-TIME OVERRIDE
    # --------------------------------------------------------

    if lead_time["priority"] == "CRITICAL":

        for authority in authorities:

            if authority["priority"] == "LOW":
                authority["priority"] = "MEDIUM"

            elif authority["priority"] == "MEDIUM":
                authority["priority"] = "HIGH"

    # --------------------------------------------------------
    # SORT AUTHORITIES
    # --------------------------------------------------------

    priority_order = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    authorities.sort(
        key=lambda x: priority_order.get(
            x["priority"],
            0
        ),
        reverse=True
    )

    return {
        "warning_level": warning_level,
        "lead_time": lead_time,
        "population_score":
            round(population_score, 4),
        "infrastructure_score":
            round(infrastructure_score, 4),
        "authority_count":
            len(authorities),
        "authorities": authorities,
    }


# ============================================================
# COMPLETE PRIORITY EVALUATION
# ============================================================

def evaluate_authority_priority(
    warning_level: str,
    lead_time_hours: Optional[float],
    population_score: float = 0.0,
    infrastructure_score: float = 0.0,
):
    """
    Main function used later by the dispatch engine.
    """

    result = get_authority_priority(
        warning_level=warning_level,
        lead_time_hours=lead_time_hours,
        population_score=population_score,
        infrastructure_score=infrastructure_score,
    )

    # Overall operational priority
    if any(
        a["priority"] == "CRITICAL"
        for a in result["authorities"]
    ):
        overall_priority = "CRITICAL"

    elif any(
        a["priority"] == "HIGH"
        for a in result["authorities"]
    ):
        overall_priority = "HIGH"

    elif any(
        a["priority"] == "MEDIUM"
        for a in result["authorities"]
    ):
        overall_priority = "MEDIUM"

    else:
        overall_priority = "LOW"

    result["overall_priority"] = overall_priority

    return result


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AUTHORITY PRIORITY / LEAD-TIME TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # TEST 1 — EARLY HIGH WARNING
    # --------------------------------------------------------

    result = evaluate_authority_priority(
        warning_level="HIGH",
        lead_time_hours=6,
        population_score=0.8,
        infrastructure_score=0.75,
    )

    print("\nTEST 1: HIGH / 6 HOURS")
    print(result)

    # --------------------------------------------------------
    # TEST 2 — EMERGENCY
    # --------------------------------------------------------

    result = evaluate_authority_priority(
        warning_level="EMERGENCY",
        lead_time_hours=2,
        population_score=0.9,
        infrastructure_score=0.95,
    )

    print("\nTEST 2: EMERGENCY / 2 HOURS")
    print(result)

    # --------------------------------------------------------
    # TEST 3 — WATCH / EARLY
    # --------------------------------------------------------

    result = evaluate_authority_priority(
        warning_level="WATCH",
        lead_time_hours=12,
        population_score=0.4,
        infrastructure_score=0.3,
    )

    print("\nTEST 3: WATCH / 12 HOURS")
    print(result)

    print("\n" + "=" * 60)