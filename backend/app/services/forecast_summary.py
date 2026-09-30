def generate_forecast_summary(
    cyclone,
    impact,
    alerts,
    historical
):

    risk_level = impact["risk_level"]

    alert_count = len(alerts)

    similar = historical["similar_cyclones"]

    if similar:
        closest = similar[0]

        historical_message = (
            f"The current cyclone has characteristics "
            f"similar to {closest['name']} ({closest['year']}) "
            f"with a similarity score of "
            f"{closest['similarity_percentage']:.2f}%."
        )
    else:
        historical_message = (
            "No sufficiently similar historical cyclone "
            "was found for this region."
        )

    return {
        "title": f"{risk_level} Cyclone Impact Risk",

        "summary": (
            f"{cyclone['name']} currently has a "
            f"{impact['risk_percentage']}% estimated "
            f"impact risk for the selected location."
        ),

        "risk_level": risk_level,

        "alert_count": alert_count,

        "historical_summary": historical_message
    }