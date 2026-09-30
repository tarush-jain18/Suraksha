import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

from app.services.authority_registry import get_authorities


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


DISPATCH_MODE = os.getenv(
    "DISPATCH_MODE",
    "mock"
).lower()

EMAIL_ENABLED = os.getenv(
    "EMAIL_ENABLED",
    "true"
).lower() == "true"

SMS_ENABLED = os.getenv(
    "SMS_ENABLED",
    "false"
).lower() == "true"

WEBHOOK_ENABLED = os.getenv(
    "WEBHOOK_ENABLED",
    "false"
).lower() == "true"


GMAIL_ADDRESS = os.getenv(
    "GMAIL_ADDRESS",
    ""
)

GMAIL_APP_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD",
    ""
)


# ============================================================
# DISPATCH LOG
# ============================================================

DISPATCH_LOG_DIR = Path(
    "data/processed/dispatch_logs"
)

DISPATCH_LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def _now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_name(value):
    return (
        str(value)
        .replace(" ", "_")
        .replace("/", "_")
        .lower()
    )


# ============================================================
# EMAIL MESSAGE BUILDER
# ============================================================

def _build_email_body(
    cyclone_name,
    location_name,
    warning_level,
    advisory,
):
    title = advisory.get(
        "title",
        f"{warning_level} Cyclone Warning"
    )

    summary = advisory.get(
        "summary",
        ""
    )

    flash_message = advisory.get(
        "flash_message",
        ""
    )

    risk_status = advisory.get(
        "risk_status",
        {}
    )

    hazard_impacts = advisory.get(
        "hazard_impacts",
        []
    )

    authority_actions = advisory.get(
        "authority_actions",
        []
    )

    priority_actions = advisory.get(
        "priority_actions",
        []
    )

    current_risk = risk_status.get(
        "current_risk",
        "N/A"
    )

    projected_risk = risk_status.get(
        "projected_risk",
        "N/A"
    )

    lead_time = risk_status.get(
        "lead_time_hours",
        "N/A"
    )

    lines = [
        "=" * 60,
        "CYCLONE EARLY WARNING",
        "=" * 60,
        "",
        f"Cyclone: {cyclone_name}",
        f"Location: {location_name}",
        f"Warning Level: {warning_level}",
        "",
        f"Title: {title}",
        "",
        "SUMMARY",
        "-" * 40,
        summary,
        "",
        "RISK STATUS",
        "-" * 40,
        f"Current Risk: {current_risk}",
        f"Projected Risk: {projected_risk}",
        f"Lead Time: {lead_time} hours",
        "",
        "HAZARD IMPACTS",
        "-" * 40,
    ]

    for hazard in hazard_impacts:
        name = hazard.get(
            "hazard",
            "Unknown"
        )

        severity = hazard.get(
            "severity",
            "UNKNOWN"
        )

        message = hazard.get(
            "message",
            ""
        )

        lines.append(
            f"- {name.upper()} [{severity}]: {message}"
        )

    lines.extend([
        "",
        "AUTHORITY ACTIONS",
        "-" * 40,
    ])

    for action in authority_actions:
        lines.append(
            f"- {action}"
        )

    lines.extend([
        "",
        "PRIORITY ACTIONS",
        "-" * 40,
    ])

    for action in priority_actions:
        lines.append(
            f"- {action}"
        )

    lines.extend([
        "",
        "FLASH MESSAGE",
        "-" * 40,
        flash_message,
        "",
        "=" * 60,
        "Automated Cyclone Impact Forecaster",
        "=" * 60,
    ])

    return "\n".join(lines)


# ============================================================
# REAL GMAIL DISPATCH
# ============================================================

def send_email(
    authority,
    advisory,
    cyclone_name="Cyclone",
    location_name="Unknown",
    warning_level="WARNING",
):
    """
    Send a REAL email using Gmail SMTP.

    Requires:
        GMAIL_ADDRESS
        GMAIL_APP_PASSWORD
    """

    recipient = authority.get(
        "email"
    )

    if not recipient:
        return {
            "success": False,
            "channel": "email",
            "status": "MISSING_RECIPIENT",
            "recipient": None,
        }

    if not EMAIL_ENABLED:
        return {
            "success": False,
            "channel": "email",
            "status": "EMAIL_DISABLED",
            "recipient": recipient,
        }

    if not GMAIL_ADDRESS:
        return {
            "success": False,
            "channel": "email",
            "status": "GMAIL_ADDRESS_NOT_CONFIGURED",
            "recipient": recipient,
        }

    if not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "channel": "email",
            "status": "GMAIL_APP_PASSWORD_NOT_CONFIGURED",
            "recipient": recipient,
        }

    subject = advisory.get(
        "title",
        f"{warning_level} Cyclone Warning for {location_name}"
    )

    body = _build_email_body(
        cyclone_name=cyclone_name,
        location_name=location_name,
        warning_level=warning_level,
        advisory=advisory,
    )

    print("\n" + "-" * 60)
    print("REAL GMAIL DISPATCH")
    print("-" * 60)
    print(f"FROM: {GMAIL_ADDRESS}")
    print(f"TO: {recipient}")
    print(f"SUBJECT: {subject}")

    try:

        message = EmailMessage()

        message["From"] = GMAIL_ADDRESS
        message["To"] = recipient
        message["Subject"] = subject

        message.set_content(body)

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30,
        ) as smtp:

            smtp.ehlo()

            smtp.starttls()

            smtp.ehlo()

            smtp.login(
                GMAIL_ADDRESS,
                GMAIL_APP_PASSWORD,
            )

            smtp.send_message(
                message
            )

        print("EMAIL SENT SUCCESSFULLY")

        return {
            "success": True,
            "channel": "email",
            "status": "EMAIL_SENT",
            "recipient": recipient,
            "provider": "gmail",
        }

    except Exception as e:

        print(
            f"EMAIL FAILED: {e}"
        )

        return {
            "success": False,
            "channel": "email",
            "status": "EMAIL_FAILED",
            "recipient": recipient,
            "provider": "gmail",
            "error": str(e),
        }


# ============================================================
# MOCK SMS
# ============================================================

def send_sms(
    authority,
    advisory,
):
    """
    SMS remains MOCK for now.
    """

    recipient = authority.get(
        "phone"
    )

    if not SMS_ENABLED:

        return {
            "success": False,
            "channel": "sms",
            "status": "SMS_DISABLED",
            "recipient": recipient,
        }

    message = advisory.get(
        "flash_message",
        advisory.get(
            "summary",
            ""
        )
    )

    print("\n" + "-" * 50)
    print("MOCK SMS DISPATCH")
    print("-" * 50)

    print(
        f"TO: {recipient}"
    )

    print(
        f"MESSAGE: {message}"
    )

    return {
        "success": True,
        "channel": "sms",
        "status": "MOCK_SENT",
        "recipient": recipient,
    }


# ============================================================
# MOCK WEBHOOK
# ============================================================

def send_webhook(
    authority,
    advisory,
):
    """
    Webhook remains MOCK for now.
    """

    if not WEBHOOK_ENABLED:

        return {
            "success": False,
            "channel": "webhook",
            "status": "WEBHOOK_DISABLED",
            "recipient": authority.get(
                "authority_id"
            ),
        }

    payload = {
        "authority": authority.get(
            "authority_id"
        ),
        "advisory": advisory,
    }

    print("\n" + "-" * 50)
    print("MOCK WEBHOOK DISPATCH")
    print("-" * 50)

    print(
        json.dumps(
            payload,
            indent=2
        )
    )

    return {
        "success": True,
        "channel": "webhook",
        "status": "MOCK_SENT",
        "recipient": authority.get(
            "authority_id"
        ),
    }


# ============================================================
# CHANNEL ROUTER
# ============================================================

def dispatch_to_authority(
    authority,
    advisory,
    cyclone_name="Cyclone",
    location_name="Unknown",
    warning_level="WARNING",
):
    """
    Dispatch advisory through every configured
    channel for the authority.
    """

    results = []

    channels = authority.get(
        "channels",
        []
    )

    for channel in channels:

        if channel == "email":

            if DISPATCH_MODE == "live":

                result = send_email(
                    authority=authority,
                    advisory=advisory,
                    cyclone_name=cyclone_name,
                    location_name=location_name,
                    warning_level=warning_level,
                )

            else:

                # Mock email mode
                recipient = authority.get(
                    "email"
                )

                print("\n" + "-" * 50)
                print("MOCK EMAIL DISPATCH")
                print("-" * 50)

                print(
                    f"TO: {recipient}"
                )

                print(
                    f"SUBJECT: {advisory.get('title')}"
                )

                print(
                    f"MESSAGE:\n{advisory.get('summary', '')}"
                )

                result = {
                    "success": True,
                    "channel": "email",
                    "status": "MOCK_SENT",
                    "recipient": recipient,
                }

        elif channel == "sms":

            result = send_sms(
                authority,
                advisory,
            )

        elif channel == "webhook":

            result = send_webhook(
                authority,
                advisory,
            )

        else:

            result = {
                "success": False,
                "channel": channel,
                "status": "UNSUPPORTED_CHANNEL",
            }

        results.append(
            result
        )

    return results


# ============================================================
# AUTHORITY SELECTION
# ============================================================

def get_dispatch_targets(
    district,
    authority_decisions,
):

    targets = []

    for decision in authority_decisions:

        authority_type = decision.get(
            "authority_type"
        )

        authorities = get_authorities(
            district=district,
            authority_type=authority_type,
        )

        for authority in authorities:

            targets.append({
                "authority": authority,
                "priority": decision.get(
                    "priority",
                    "LOW"
                ),
                "reason": decision.get(
                    "reason"
                ),
            })

    return targets


# ============================================================
# DISPATCH LOG
# ============================================================

def save_dispatch_log(
    cyclone_name,
    location_name,
    warning_level,
    advisory,
    dispatch_results,
):

    timestamp = _now()

    log_entry = {
        "timestamp": timestamp,
        "cyclone_name": cyclone_name,
        "location_name": location_name,
        "warning_level": warning_level,
        "dispatch_mode": DISPATCH_MODE,
        "advisory": advisory,
        "dispatch_results": dispatch_results,
    }

    filename = (
        f"{_safe_name(cyclone_name)}_"
        f"{_safe_name(location_name)}_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        f".json"
    )

    path = (
        DISPATCH_LOG_DIR /
        filename
    )

    with open(
        path,
        "w"
    ) as f:

        json.dump(
            log_entry,
            f,
            indent=2
        )

    return str(path)


# ============================================================
# MAIN DISPATCH FUNCTION
# ============================================================

def dispatch_authority_advisory(
    cyclone_name,
    location_name,
    district,
    warning_level,
    advisory,
    authority_decisions,
):

    targets = get_dispatch_targets(
        district=district,
        authority_decisions=authority_decisions,
    )

    dispatch_results = []

    for target in targets:

        authority = target[
            "authority"
        ]

        print("\n")
        print("=" * 60)
        print("AUTHORITY DISPATCH")
        print("=" * 60)

        print(
            f"Authority: {authority['name']}"
        )

        print(
            f"Type: {authority['authority_type']}"
        )

        print(
            f"Priority: {target['priority']}"
        )

        results = dispatch_to_authority(
            authority=authority,
            advisory=advisory,
            cyclone_name=cyclone_name,
            location_name=location_name,
            warning_level=warning_level,
        )

        dispatch_results.append({
            "authority_id":
                authority["authority_id"],

            "authority_name":
                authority["name"],

            "authority_type":
                authority["authority_type"],

            "priority":
                target["priority"],

            "reason":
                target.get("reason"),

            "channels":
                results,
        })

    log_path = save_dispatch_log(
        cyclone_name=cyclone_name,
        location_name=location_name,
        warning_level=warning_level,
        advisory=advisory,
        dispatch_results=dispatch_results,
    )

    successful_channels = 0

    failed_channels = 0

    for authority_result in dispatch_results:

        for channel in authority_result[
            "channels"
        ]:

            if channel.get(
                "success"
            ):

                successful_channels += 1

            else:

                failed_channels += 1

    return {
        "success": (
            successful_channels > 0
        ),

        "dispatch_mode":
            DISPATCH_MODE,

        "cyclone_name":
            cyclone_name,

        "location_name":
            location_name,

        "warning_level":
            warning_level,

        "authority_count":
            len(dispatch_results),

        "successful_channels":
            successful_channels,

        "failed_channels":
            failed_channels,

        "dispatch_results":
            dispatch_results,

        "log_file":
            log_path,
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AUTOMATED DISPATCH ENGINE TEST")
    print("=" * 60)

    print(
        f"DISPATCH MODE: {DISPATCH_MODE}"
    )

    advisory = {
    "title": "HIGH Cyclone Warning for Puri",

    "severity": "HIGH",

    "summary": (
        "Demo Cyclone is currently at WATCH risk for Puri. "
        "Backend projections indicate HIGH risk within 6 hours."
    ),

    "flash_message": (
        "HIGH WARNING: Demo Cyclone projected to reach "
        "HIGH risk in approximately 6 hours."
    ),

    "risk_status": {
        "current_risk": 0.48,
        "projected_risk": 0.65,
        "lead_time_hours": 6
    },

    "hazard_impacts": [
        {
            "hazard": "Flood",
            "severity": "HIGH",
            "message": "Flood hazard is projected to increase significantly."
        },
        {
            "hazard": "Storm Surge",
            "severity": "HIGH",
            "message": "Storm surge risk is elevated for coastal areas."
        },
        {
            "hazard": "Wind",
            "severity": "MODERATE",
            "message": "Wind hazard is expected to increase over the forecast period."
        }
    ],

    "authority_actions": [
        "Activate district-level disaster preparedness.",
        "Review evacuation and shelter readiness.",
        "Prepare emergency response teams.",
        "Monitor vulnerable coastal and low-lying areas."
    ],

    "priority_actions": [
        "Prepare evacuation resources.",
        "Alert emergency response teams.",
        "Inspect critical infrastructure.",
        "Maintain continuous cyclone monitoring."
    ]
}
    authority_decisions = [

        {
            "authority_type":
                "DISTRICT_DISASTER_MANAGEMENT",

            "priority":
                "HIGH",

            "reason":
                "High-level cyclone risk requires "
                "district disaster coordination.",
        },

        {
            "authority_type":
                "MUNICIPAL_AUTHORITY",

            "priority":
                "HIGH",

            "reason":
                "Municipal authorities may need "
                "to prepare local response operations.",
        },

        {
            "authority_type":
                "BLOCK_ADMINISTRATION",

            "priority":
                "HIGH",

            "reason":
                "Population exposure requires "
                "local administrative coordination.",
        },

        {
            "authority_type":
                "LOCAL_EMERGENCY_SERVICES",

            "priority":
                "HIGH",

            "reason":
                "Infrastructure exposure may require "
                "local emergency response readiness.",
        },
    ]

    result = dispatch_authority_advisory(

        cyclone_name="Demo Cyclone",

        location_name="Puri",

        district="Puri",

        warning_level="HIGH",

        advisory=advisory,

        authority_decisions=
            authority_decisions,
    )

    print("\n")
    print("=" * 60)
    print("FINAL DISPATCH RESULT")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=2
        )
    )