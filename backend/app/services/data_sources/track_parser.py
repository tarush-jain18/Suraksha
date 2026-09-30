import re
from pathlib import Path

import cv2
import pytesseract


TRACK_DIR = Path("data/raw/imd/tracks")
OUTPUT_DIR = TRACK_DIR / "processed"


def load_image(path):
    image = cv2.imread(str(path))

    if image is None:
        raise FileNotFoundError(
            f"Could not open image: {path}"
        )

    return image


def upscale_image(image, scale=4):
    return cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )


def run_ocr(image):
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    text = pytesseract.image_to_string(
        otsu,
        config="--psm 6"
    )

    return text


def extract_track_labels(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    track_points = []

    pattern = re.compile(
        r"(\d{1,2}/\d{1,2})"
        r"\s*,?\s*"
        r"(\d{1,3})\s*KT",
        re.IGNORECASE
    )

    for line in lines:

        match = pattern.search(line)

        if not match:
            continue

        date_time = match.group(1)
        wind_kt = float(match.group(2))

        day, hour = date_time.split("/")

        track_points.append({
            "date": int(day),
            "hour_utc": int(hour),
            "wind_kt": wind_kt,
            "wind_kmph": round(
                wind_kt * 1.852,
                1
            ),
            "latitude": None,
            "longitude": None,
            "coordinate_source": "not_available_from_ocr"
        })

    return track_points


def extract_pressure(text):

    pattern = re.compile(
        r"(\d{3,4})\s*hPa",
        re.IGNORECASE
    )

    values = []

    for value in pattern.findall(text):

        pressure = float(value)

        if 850 <= pressure <= 1100:
            values.append(pressure)

    return sorted(set(values))


def detect_region(text):

    upper = text.upper()

    regions = [
        "ODISHA",
        "UTTAR PRADESH",
        "WEST BENGAL",
        "ANDHRA PRADESH",
        "CHHATTISGARH",
        "MYANMAR",
        "BANGLADESH",
        "ANDAMAN"
    ]

    detected = []

    for region in regions:

        if region in upper:
            detected.append(region)

    return detected


def classify_odisha_relevance(text):

    upper = text.upper()

    if "ODISHA" in upper:
        return True

    if "ORISSA" in upper:
        return True

    return False


def parse_track_image(image_path):

    print("=" * 70)
    print("IMD TRACK PRODUCT PARSER")
    print("=" * 70)

    print("Image:", image_path)

    image = load_image(
        image_path
    )

    print(
        "Original size:",
        image.shape[1],
        "x",
        image.shape[0]
    )

    image = upscale_image(
        image,
        scale=4
    )

    print(
        "Upscaled size:",
        image.shape[1],
        "x",
        image.shape[0]
    )

    text = run_ocr(
        image
    )

    print("\n===== DETECTED REGION =====")

    regions = detect_region(
        text
    )

    print(regions)

    odisha_relevant = classify_odisha_relevance(
        text
    )

    print(
        "Odisha relevant:",
        odisha_relevant
    )

    print("\n===== TRACK LABELS =====")

    track_points = extract_track_labels(
        text
    )

    if not track_points:

        print(
            "No track labels detected."
        )

    else:

        for point in track_points:

            print(
                f"{point['date']:02d}/"
                f"{point['hour_utc']:02d} UTC"
                f" | "
                f"{point['wind_kt']} KT"
                f" | "
                f"{point['wind_kmph']} km/h"
            )

    print("\n===== PRESSURE =====")

    pressure = extract_pressure(
        text
    )

    print(pressure)

    result = {
        "source": "IMD Observed & Forecast Track",
        "image": str(image_path),
        "detected_regions": regions,
        "odisha_relevant": odisha_relevant,
        "coordinates_available": False,
        "track_points": track_points,
        "pressure_hpa": pressure,
        "raw_ocr_available": True
    }

    return result


def save_result(result):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        OUTPUT_DIR /
        "candidate_1_parsed.json"
    )

    import json

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\n===== RESULT SAVED =====")
    print(output_path)

    return output_path


if __name__ == "__main__":

    image_path = (
        TRACK_DIR /
        "candidate_1.png"
    )

    if not image_path.exists():

        print(
            "Track image not found:",
            image_path
        )

        raise SystemExit(1)

    result = parse_track_image(
        image_path
    )

    save_result(
        result
    )