def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0
) -> float:

    return max(
        minimum,
        min(float(value), maximum)
    )


def normalize(
    value: float,
    minimum: float,
    maximum: float
) -> float:

    if maximum <= minimum:
        return 0.0

    score = (
        float(value) - minimum
    ) / (
        maximum - minimum
    )

    return clamp(score)


def classify_risk(
    risk_score: float
) -> str:

    if risk_score < 0.20:
        return "LOW"

    elif risk_score < 0.40:
        return "MODERATE"

    elif risk_score < 0.60:
        return "HIGH"

    elif risk_score < 0.80:
        return "VERY HIGH"

    return "EXTREME"


def calculate_exposure(
    population_density: float,
    infrastructure_density: float,
    agriculture_percentage: float
) -> float:

    population_score = normalize(
        population_density,
        0,
        500
    )

    infrastructure_score = normalize(
        infrastructure_density,
        0,
        30
    )

    agriculture_score = normalize(
        agriculture_percentage,
        0,
        60
    )

    exposure = (
        0.45 * population_score
        + 0.35 * infrastructure_score
        + 0.20 * agriculture_score
    )

    return round(
        clamp(exposure),
        4
    )


def calculate_vulnerability(
    population_vulnerability: float,
    infrastructure_vulnerability: float,
    agriculture_vulnerability: float,
    healthcare_vulnerability: float
) -> float:

    vulnerability = (
        0.30 * population_vulnerability
        + 0.30 * infrastructure_vulnerability
        + 0.20 * agriculture_vulnerability
        + 0.20 * healthcare_vulnerability
    )

    return round(
        clamp(vulnerability),
        4
    )


def calculate_risk_score(
    hazard: float,
    exposure: float,
    vulnerability: float
) -> float:

    hazard = clamp(hazard)
    exposure = clamp(exposure)
    vulnerability = clamp(vulnerability)

    # Exposure and vulnerability act as
    # impact modifiers instead of directly
    # multiplying the hazard down to near zero.

    exposure_modifier = (
        0.60
        + 0.40 * exposure
    )

    vulnerability_modifier = (
        0.60
        + 0.40 * vulnerability
    )

    risk = (
        hazard
        * exposure_modifier
        * vulnerability_modifier
    )

    return round(
        clamp(risk),
        4
    )


def get_risk_drivers(
    hazards: dict
):

    drivers = []

    if hazards.get("wind", 0) >= 0.6:
        drivers.append(
            "High wind exposure"
        )

    if hazards.get("rainfall", 0) >= 0.6:
        drivers.append(
            "Heavy rainfall"
        )

    if hazards.get("storm_surge", 0) >= 0.6:
        drivers.append(
            "Storm surge"
        )

    if hazards.get("flood", 0) >= 0.6:
        drivers.append(
            "Flooding"
        )

    if not drivers:
        drivers.append(
            "No major hazard driver"
        )

    return drivers