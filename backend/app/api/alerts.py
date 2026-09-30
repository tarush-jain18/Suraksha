from fastapi import APIRouter

from app.services.alert_engine import generate_alerts


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"]
)


@router.get("/")
def get_alerts(
    risk_score: float,
    wind: float,
    rainfall: float,
    storm_surge: float,
    flood: float
):
    hazards = {
        "wind": wind,
        "rainfall": rainfall,
        "storm_surge": storm_surge,
        "flood": flood
    }

    alerts = generate_alerts(
        risk_score,
        hazards
    )

    return {
        "success": True,
        "alerts": alerts
    }