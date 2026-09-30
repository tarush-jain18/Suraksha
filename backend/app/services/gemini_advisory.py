# ============================================================
# GEMINI ADVISORY ENGINE
# ============================================================

import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_MODEL = "gemini-3.8-flash"


# ============================================================
# CLIENT
# ============================================================

def get_gemini_client():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# BUILD ADVISORY PROMPT
# ============================================================

def build_advisory_prompt(
    risk_result,
    infrastructure_exposure=None,
    population_data=None,
    early_warnings=None
):
    """
    Build a structured prompt for Gemini.

    Gemini explains the results produced by the backend.
    It does not recalculate cyclone risk.
    """

    cyclone = risk_result.get(
        "cyclone",
        {}
    )

    location = risk_result.get(
        "location",
        {}
    )

    hazards = risk_result.get(
        "hazards",
        {}
    )

    impact = risk_result.get(
        "impact",
        {}
    )

    track_forecast = risk_result.get(
        "track_forecast",
        {}
    )

    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    context = {
        "cyclone": cyclone,
        "location": location,
        "hazards": hazards,
        "impact": impact,
        "track_forecast": track_forecast,
        "population": population_data or {},
        "infrastructure": infrastructure_exposure or {},
        "early_warnings": early_warnings or {}
    }

    context_json = json.dumps(
        context,
        indent=2,
        default=str
    )

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are the advisory generation component of a
cyclone impact forecasting system.

Your job is to convert the backend's calculated
cyclone information into a clear, concise and
actionable public advisory.

IMPORTANT RULES:

1. Do NOT recalculate risk or hazard scores.
2. Do NOT invent weather values.
3. Do NOT invent population numbers.
4. Do NOT invent infrastructure counts.
5. Use only the information provided below.
6. Treat the backend calculations as authoritative.
7. Clearly distinguish between detected risk and
   recommended safety actions.
8. Use simple language suitable for the general public.
9. Do not use unnecessarily technical terminology.
10. Do not claim that an evacuation is required unless
    the supplied alerts or official instructions indicate it.
11. If information is missing, do not make it up.
12. Keep the advisory concise.

BACKEND DATA:

{context_json}


Generate the advisory in the following JSON structure:

{{
    "title": "Short advisory title",

    "severity": "LOW | WATCH | MODERATE | HIGH | EMERGENCY",

    "summary": "2-3 sentence summary of the current situation",

    "hazards": [
        {{
            "hazard": "Hazard name",
            "severity": "LOW | WATCH | MODERATE | HIGH | EMERGENCY",
            "message": "Short explanation"
        }}
    ],

    "population_impact": "Short explanation of population exposure",

    "infrastructure_impact": "Short explanation of infrastructure exposure",

    "recommended_actions": [
        "Action 1",
        "Action 2",
        "Action 3"
    ],

    "flash_message": "One short message suitable for a frontend notification"
}}

Return ONLY valid JSON.
"""


    return prompt


# ============================================================
# GENERATE ADVISORY
# ============================================================

def generate_gemini_advisory(
    risk_result,
    infrastructure_exposure=None,
    population_data=None,
    early_warnings=None
):
    """
    Generate a Gemini-powered cyclone advisory.
    """

    if not risk_result:
        return {
            "success": False,
            "error": "Risk result is missing.",
            "advisory": None
        }

    try:

        client = get_gemini_client()

        prompt = build_advisory_prompt(
            risk_result=risk_result,
            infrastructure_exposure=infrastructure_exposure,
            population_data=population_data,
            early_warnings=early_warnings
        )

        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt
        )

        text = interaction.output_text.strip()

        # ----------------------------------------------------
        # REMOVE MARKDOWN CODE FENCES IF GEMINI ADDS THEM
        # ----------------------------------------------------

        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        advisory = json.loads(
            text
        )

        return {
            "success": True,
            "model": GEMINI_MODEL,
            "advisory": advisory
        }

    except json.JSONDecodeError:

        return {
            "success": False,
            "model": GEMINI_MODEL,
            "error": "Gemini returned invalid JSON.",
            "raw_response": text if "text" in locals() else None,
            "advisory": None
        }

    except Exception as e:

        return {
            "success": False,
            "model": GEMINI_MODEL,
            "error": str(e),
            "advisory": None
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

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

        "hazards": {
            "wind": 0.85,
            "rainfall": 0.72,
            "storm_surge": 0.65,
            "flood": 0.78
        },

        "track_forecast": {
            "risk_score": 0.70
        }
    }

    test_population = {
        "population_density": 650
    }

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

    test_warnings = {
        "highest_alert_level": "EMERGENCY",
        "alert_count": 13
    }

    print()
    print("=" * 60)
    print("GEMINI ADVISORY TEST")
    print("=" * 60)

    result = generate_gemini_advisory(
        risk_result=test_risk_result,
        infrastructure_exposure=test_infrastructure,
        population_data=test_population,
        early_warnings=test_warnings
    )

    print()

    print(
        json.dumps(
            result,
            indent=2
        )
    )