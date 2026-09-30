from pathlib import Path
import json


REGISTRY_FILE = Path(
    "data/processed/authority_registry.json"
)


DEFAULT_AUTHORITIES = [
    {
        "authority_id": "odisha_ddma",
        "authority_type": "DISTRICT_DISASTER_MANAGEMENT",
        "name": "District Disaster Management Authority",
        "district": "Puri",
        "email": "ddma.puri@example.gov.in",
        "phone": "+91XXXXXXXXXX",
        "channels": ["email", "sms"],
        "active": True,
    },
    {
        "authority_id": "puri_municipality",
        "authority_type": "MUNICIPAL_AUTHORITY",
        "name": "Puri Municipal Authority",
        "district": "Puri",
        "email": "municipality.puri@example.gov.in",
        "phone": "+91XXXXXXXXXX",
        "channels": ["email", "sms"],
        "active": True,
    },
    {
        "authority_id": "puri_block",
        "authority_type": "BLOCK_ADMINISTRATION",
        "name": "Puri Block Administration",
        "district": "Puri",
        "email": "block.puri@example.gov.in",
        "phone": "+91XXXXXXXXXX",
        "channels": ["email"],
        "active": True,
    },
    {
        "authority_id": "puri_emergency",
        "authority_type": "LOCAL_EMERGENCY_SERVICES",
        "name": "Puri Emergency Services",
        "district": "Puri",
        "email": "emergency.puri@example.gov.in",
        "phone": "+91XXXXXXXXXX",
        "channels": ["sms"],
        "active": True,
    },
]


def initialize_registry():
    """Create the authority registry if it doesn't exist."""

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not REGISTRY_FILE.exists():

        with open(REGISTRY_FILE, "w") as f:
            json.dump(
                DEFAULT_AUTHORITIES,
                f,
                indent=2
            )

        return DEFAULT_AUTHORITIES

    return load_registry()


def load_registry():
    """Load all registered authorities."""

    if not REGISTRY_FILE.exists():
        return initialize_registry()

    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)


def get_authorities(
    district=None,
    authority_type=None
):
    """
    Return active authorities matching
    district and/or authority type.
    """

    authorities = load_registry()

    results = []

    for authority in authorities:

        if not authority.get("active", False):
            continue

        if (
            district
            and authority.get("district", "").lower()
            != district.lower()
        ):
            continue

        if (
            authority_type
            and authority.get("authority_type")
            != authority_type
        ):
            continue

        results.append(authority)

    return results


def get_authority_by_id(authority_id):
    """Return one authority by ID."""

    authorities = load_registry()

    for authority in authorities:

        if authority.get("authority_id") == authority_id:
            return authority

    return None


def get_dispatch_targets(
    district,
    authority_types
):
    """
    Convert authority priority output into
    actual registered dispatch targets.
    """

    targets = []

    for authority_type in authority_types:

        matches = get_authorities(
            district=district,
            authority_type=authority_type
        )

        for authority in matches:
            targets.append(authority)

    return targets


def add_authority(authority):
    """Add a new authority to the registry."""

    authorities = load_registry()

    authority_id = authority.get("authority_id")

    if not authority_id:
        raise ValueError(
            "authority_id is required."
        )

    if get_authority_by_id(authority_id):
        raise ValueError(
            f"Authority already exists: {authority_id}"
        )

    authorities.append(authority)

    with open(REGISTRY_FILE, "w") as f:
        json.dump(
            authorities,
            f,
            indent=2
        )

    return authority


def deactivate_authority(authority_id):
    """Disable an authority without deleting it."""

    authorities = load_registry()

    for authority in authorities:

        if authority.get("authority_id") == authority_id:

            authority["active"] = False

            with open(REGISTRY_FILE, "w") as f:
                json.dump(
                    authorities,
                    f,
                    indent=2
                )

            return authority

    return None


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AUTHORITY REGISTRY TEST")
    print("=" * 60)

    initialize_registry()

    print("\nALL PURI AUTHORITIES")

    authorities = get_authorities(
        district="Puri"
    )

    for authority in authorities:

        print(
            f"- {authority['authority_type']}: "
            f"{authority['name']}"
        )

    print("\nMUNICIPAL AUTHORITIES")

    municipal = get_authorities(
        district="Puri",
        authority_type="MUNICIPAL_AUTHORITY"
    )

    for authority in municipal:
        print(authority)

    print("\nDISPATCH TARGETS")

    targets = get_dispatch_targets(
        district="Puri",
        authority_types=[
            "DISTRICT_DISASTER_MANAGEMENT",
            "MUNICIPAL_AUTHORITY",
            "LOCAL_EMERGENCY_SERVICES",
        ]
    )

    for target in targets:

        print(
            f"{target['name']} -> "
            f"{target['channels']}"
        )

    print("\n" + "=" * 60)