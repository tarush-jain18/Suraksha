from fastapi import FastAPI

from app.api.current import router as current_router
from app.api.cyclone import router as cyclone_router
from app.api.risk import router as risk_router
from app.api.history import router as history_router
from app.api.alerts import router as alerts_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Cyclone Impact Forecaster",
    description="Track-Based Cyclone Impact & Infrastructure Vulnerability Forecaster for Odisha",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://suraksha-azure.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Current routes first so /api/cyclones/current
# is not captured by /api/cyclones/{cyclone_id}
app.include_router(current_router)

app.include_router(cyclone_router)

app.include_router(risk_router)

app.include_router(history_router)

app.include_router(alerts_router)


@app.get("/")
def root():
    return {
        "message": "Cyclone Impact Forecaster API is running",
        "region": "Odisha",
        "status": "healthy"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "region": "Odisha"
    }