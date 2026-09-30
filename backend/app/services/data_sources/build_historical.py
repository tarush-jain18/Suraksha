import json
from app.services.data_sources.ibtracs import find_odisha_cyclones

OUTPUT_FILE = "data/historical/odisha_cyclones.json"


def main():
    storms = find_odisha_cyclones()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(storms, f, indent=2)

    named = [
        storm
        for storm in storms
        if storm["name"] != "UNNAMED"
    ]

    print("Historical dataset created")
    print(f"Total records: {len(storms)}")
    print(f"Named cyclones: {len(named)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
