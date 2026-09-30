import json
import os

from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

GEMINI_MODEL = "gemini-3.8-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )

    return genai.Client(
        api_key=api_key,
        http_options={
            "api_version": "v1"
        }
    )


# ============================================================
# PROMPT
# ============================================================

def build_authority_prompt(
    cyclone_name,
    location_name,
    authority_type,
    current_risk,
    current_level,
    projected_risk,
    projected_level,
    lead_time_hours,
    hazards,
    population_score,
    infrastructure_score,
    trigger_reasons,
):
    data = {
        "cyclone_name": cyclone_name,
        "location": location_name,
        "authority_type": authority_type,

        "current_risk": round(
            float(current_risk), 3
        ),

        "current_warning_level": current_level,

        "projected_risk": round(
            float(projected_risk), 3
        ),

        "projected_warning_level": projected_level,

        "lead_time_hours": lead_time_hours,

        "hazards": hazards,

        "population_exposure_score": round(
            float(population_score), 3
        ),

        "infrastructure_exposure_score": round(
            float(infrastructure_score), 3
        ),

        "trigger_reasons": trigger_reasons,
    }

    prompt = f"""
You are an emergency-management advisory generator.

Generate a concise operational cyclone advisory for a
local disaster-management or municipal authority.

IMPORTANT RULES:

1. Do NOT calculate or change risk scores.
2. Do NOT invent weather observations.
3. Do NOT invent population numbers.
4. Do NOT invent infrastructure counts.
5. Use ONLY the supplied structured data.
6. Do NOT make claims about actions already taken.
7. Recommendations must be practical and operational.
8. The advisory is for authorities, NOT the general public.
9. Clearly distinguish current conditions from projected escalation.
10. Preserve the supplied warning levels and lead time.

STRUCTURED DATA:

{json.dumps(data, indent=2)}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "title": "short authority alert title",
  "severity": "WATCH|MODERATE|HIGH|EMERGENCY",

  "summary": "concise operational summary",

  "risk_status": {{
    "current_risk": 0.0,
    "current_level": "WATCH",
    "projected_risk": 0.0,
    "projected_level": "HIGH",
    "lead_time_hours": 0
  }},

  "hazard_impacts": [
    {{
      "hazard": "Wind",
      "severity": "HIGH",
      "message": "operational impact"
    }}
  ],

  "population_impacts":
    "brief population exposure assessment",

  "infrastructure_impacts":
    "brief infrastructure exposure assessment",

  "authority_actions": [
    "specific operational action",
    "specific operational action",
    "specific operational action"
  ],

  "priority_actions": [
    "most urgent action",
    "second urgent action"
  ],

  "flash_message":
    "one short message suitable for an emergency dashboard"
}}
"""

    return prompt


# ============================================================
# RESPONSE CLEANING
# ============================================================

def _clean_json_response(text):
    """
    Remove markdown code fences if Gemini returns them.
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ============================================================
# GENERATE ADVISORY
# ============================================================

def generate_authority_advisory(
    cyclone_name,
    location_name,
    authority_type,
    current_risk,
    current_level,
    projected_risk,
    projected_level,
    lead_time_hours,
    hazards,
    population_score,
    infrastructure_score,
    trigger_reasons,
):
    """
    Generate an operational authority advisory.

    Gemini is the communication layer.
    The deterministic backend remains the source
    of truth for risk and warning decisions.
    """

    prompt = build_authority_prompt(
        cyclone_name=cyclone_name,
        location_name=location_name,
        authority_type=authority_type,
        current_risk=current_risk,
        current_level=current_level,
        projected_risk=projected_risk,
        projected_level=projected_level,
        lead_time_hours=lead_time_hours,
        hazards=hazards,
        population_score=population_score,
        infrastructure_score=infrastructure_score,
        trigger_reasons=trigger_reasons,
    )

    client = get_gemini_client()

    try:

        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
        )

        text = interaction.output_text.strip()

        text = _clean_json_response(text)

        advisory = json.loads(text)

        # --------------------------------------------------
        # Force backend-calculated values
        # --------------------------------------------------

        advisory["risk_status"] = {
            "current_risk": round(
                float(current_risk), 3
            ),
            "current_level": current_level,
            "projected_risk": round(
                float(projected_risk), 3
            ),
            "projected_level": projected_level,
            "lead_time_hours": lead_time_hours,
        }

        advisory["severity"] = projected_level

        return {
            "success": True,
            "model": GEMINI_MODEL,
            "authority_type": authority_type,
            "location": location_name,
            "advisory": advisory,
            "fallback": False,
        }

    except Exception as exc:

        print(
            f"[WARNING] Gemini advisory unavailable: {exc}"
        )

        # --------------------------------------------------
        # SAFE FALLBACK
        # --------------------------------------------------

        fallback_advisory = {
            "title": (
                f"{projected_level} Cyclone Warning "
                f"for {location_name}"
            ),

            "severity": projected_level,

            "summary": (
                f"{cyclone_name} is currently at "
                f"{current_level} risk for {location_name}. "
                f"Backend projections indicate "
                f"{projected_level} risk within "
                f"{lead_time_hours} hours."
            ),

            "risk_status": {
                "current_risk": round(
                    float(current_risk), 3
                ),
                "current_level": current_level,
                "projected_risk": round(
                    float(projected_risk), 3
                ),
                "projected_level": projected_level,
                "lead_time_hours": lead_time_hours,
            },

            "hazard_impacts": [
                {
                    "hazard": hazard,
                    "severity": (
                        "EMERGENCY"
                        if score >= 0.80
                        else "HIGH"
                        if score >= 0.60
                        else "MODERATE"
                        if score >= 0.40
                        else "WATCH"
                    ),
                    "message": (
                        f"{hazard.replace('_', ' ').title()} "
                        f"hazard score: {score:.2f}"
                    ),
                }
                for hazard, score in hazards.items()
            ],

            "population_impacts": (
                f"Population exposure score: "
                f"{population_score:.2f}"
            ),

            "infrastructure_impacts": (
                f"Infrastructure exposure score: "
                f"{infrastructure_score:.2f}"
            ),

            "authority_actions": [
                "Review current cyclone response readiness.",
                "Verify communication channels with local response teams.",
                "Review vulnerable population and infrastructure exposure.",
                "Prepare escalation procedures if projected risk increases.",
            ],

            "priority_actions": [
                "Review the projected escalation immediately.",
                "Maintain readiness for the projected warning level.",
            ],

            "flash_message": (
                f"{projected_level} WARNING: "
                f"{cyclone_name} projected to reach "
                f"{projected_level} risk in approximately "
                f"{lead_time_hours} hours."
            ),
        }

        return {
            "success": True,
            "model": GEMINI_MODEL,
            "authority_type": authority_type,
            "location": location_name,
            "advisory": fallback_advisory,
            "fallback": True,
            "fallback_reason": str(exc),
        }

# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AUTHORITY GEMINI ADVISORY TEST")
    print("=" * 60)

    result = generate_authority_advisory(
        cyclone_name="Demo Cyclone",
        location_name="Puri",

        authority_type=
            "DISTRICT_DISASTER_MANAGEMENT",

        current_risk=0.48,
        current_level="WATCH",

        projected_risk=0.65,
        projected_level="HIGH",

        lead_time_hours=6,

        hazards={
            "wind": 0.72,
            "rainfall": 0.65,
            "storm_surge": 0.55,
            "flood": 0.68,
        },

        population_score=0.8,

        infrastructure_score=0.75,

        trigger_reasons=[
            "Projected risk is expected to reach HIGH level.",
            "Flood hazard is projected to increase significantly.",
            "High population exposure is present.",
            "Significant infrastructure exposure is present.",
        ],
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print("\n" + "=" * 60)