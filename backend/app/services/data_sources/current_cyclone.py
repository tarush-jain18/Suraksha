import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

import geopandas as gpd
import pytesseract
import requests

from bs4 import BeautifulSoup
from PIL import Image
from pypdf import PdfReader
from shapely.geometry import Point


IMD_HOME = "https://rsmcnewdelhi.imd.gov.in/"

ARCHIVE_URL = (
    "https://rsmcnewdelhi.imd.gov.in/"
    "archive-information.php"
    "?internal_menu=Ng%3D%3D&menu_id=NQ%3D%3D"
)

ODISHA_GEOJSON = Path(
    "data/geospatial/odisha.geojson"
)

TRACK_DIR = Path(
    "data/raw/imd/tracks"
)


# ============================================================
# HTTP
# ============================================================

def fetch_url(url, timeout=30):

    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "Chrome/154.0 Safari/537.36"
            )
        }
    )

    response.raise_for_status()

    return response


# ============================================================
# IMD HOMEPAGE
# ============================================================

def fetch_imd_homepage():

    response = fetch_url(
        IMD_HOME,
        timeout=20
    )

    return response.text


def get_current_bulletin_links(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = []

    for anchor in soup.find_all(
        "a",
        href=True
    ):

        text = anchor.get_text(
            " ",
            strip=True
        )

        href = urljoin(
            IMD_HOME,
            anchor["href"]
        )

        if (
            "National Bulletin" in text
            or
            "RSMC Bulletin" in text
        ):

            links.append({
                "type": text,
                "url": href
            })

    unique = []
    seen = set()

    for link in links:

        if link["url"] not in seen:

            seen.add(
                link["url"]
            )

            unique.append(
                link
            )

    return unique


def get_bulletin_by_type(
    links,
    bulletin_type
):

    for link in links:

        if link["type"] == bulletin_type:

            return link

    return None


def download_bulletin(url):

    response = fetch_url(
        url,
        timeout=30
    )

    print("\n===== BULLETIN =====")
    print("URL:", url)
    print("Status:", response.status_code)
    print(
        "Content-Type:",
        response.headers.get(
            "content-type"
        )
    )
    print(
        "Size:",
        len(response.content)
    )

    return response.content


# ============================================================
# PDF HELPERS
# ============================================================

def extract_pdf_text(pdf_content):

    reader = PdfReader(
        BytesIO(pdf_content)
    )

    pages = []

    for page in reader.pages:

        pages.append(
            page.extract_text() or ""
        )

    return "\n".join(
        pages
    )


def clean_text(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ============================================================
# COORDINATES
# ============================================================

def extract_coordinates(text):

    patterns = [

        r"(\d{1,2}(?:\.\d+)?)\s*°?\s*N"
        r"\s*[/,]\s*"
        r"(\d{1,3}(?:\.\d+)?)\s*°?\s*E",

        r"(\d{1,2}(?:\.\d+)?)\s*N"
        r"\s+"
        r"(\d{1,3}(?:\.\d+)?)\s*E",

        r"(\d{1,2}(?:\.\d+)?)\s*°\s*N"
        r".{0,40}?"
        r"(\d{1,3}(?:\.\d+)?)\s*°\s*E"
    ]

    found = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        for latitude, longitude in matches:

            coordinate = {
                "latitude": float(
                    latitude
                ),
                "longitude": float(
                    longitude
                )
            }

            if coordinate not in found:

                found.append(
                    coordinate
                )

    return found


# ============================================================
# NATIONAL BULLETIN
# ============================================================

def extract_national_system_type(text):

    patterns = [

        r"Sub:\s*(.*?)(?:\n|It is very likely)",

        r"Sub:\s*(.*?)(?:It is very likely)"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            return clean_text(
                match.group(1)
            )

    return None


def extract_issue_time(text):

    patterns = [

        r"TIME OF ISSUE:\s*(.*?)\s+Dated:\s*(\d{2}\.\d{2}\.\d{4})",

        r"issued at\s*(\d{3,4})\s*UTC\s*(\d{2}\.\d{2}\.\d{4})"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            return {
                "time":
                    match.group(1).strip(),

                "date":
                    match.group(2).strip()
            }

    return None


def extract_movement(text):

    patterns = [

        r"very likely to move\s+([a-z-]+(?:wards)?)",

        r"likely to move\s+([a-z-]+(?:wards)?)",

        r"move\s+([a-z-]+(?:wards)?)"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(
                1
            ).lower()

    return None


def extract_affected_regions(text):

    regions = []

    match = re.search(
        r"Impact expected\s*\((.*?)\)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:

        return regions

    value = clean_text(
        match.group(1)
    )

    for region in re.split(
        r",| and ",
        value
    ):

        region = region.strip()

        if region:

            regions.append(
                region
            )

    return regions


def extract_warning_text(text):

    warnings = []

    rainfall_match = re.search(
        r"\(i\)\s*Rainfall Warning:(.*?)(?=\(ii\)|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if rainfall_match:

        warnings.append({
            "type": "rainfall",
            "text": clean_text(
                rainfall_match.group(1)
            )
        })

    wind_match = re.search(
        r"\(ii\)\s*Wind warning:(.*?)(?=\(iii\)|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if wind_match:

        warnings.append({
            "type": "wind",
            "text": clean_text(
                wind_match.group(1)
            )
        })

    return warnings


def parse_national_bulletin(
    pdf_content
):

    text = extract_pdf_text(
        pdf_content
    )

    return {

        "source":
            "IMD National Bulletin",

        "system_type":
            extract_national_system_type(
                text
            ),

        "coordinates":
            extract_coordinates(
                text
            ),

        "movement":
            extract_movement(
                text
            ),

        "issue_time":
            extract_issue_time(
                text
            ),

        "affected_regions":
            extract_affected_regions(
                text
            ),

        "warnings":
            extract_warning_text(
                text
            )
    }


# ============================================================
# RSMC PARSING
# ============================================================

def extract_pressure(text):

    patterns = [

        r"estimated\s+central\s+pressure\s+is\s+"
        r"(\d+(?:\.\d+)?)\s*hPa",

        r"central\s+pressure\s+of\s+"
        r"(\d+(?:\.\d+)?)\s*hPa",

        r"pressure\s+is\s+"
        r"(\d+(?:\.\d+)?)\s*hPa"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return float(
                match.group(1)
            )

    return None


def extract_wind(text):

    patterns = [

        r"associated\s+maximum\s+sustained\s+wind"
        r".{0,120}?"
        r"(\d+(?:\.\d+)?)\s*kt",

        r"maximum\s+sustained\s+wind"
        r".{0,120}?"
        r"(\d+(?:\.\d+)?)\s*kt"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            knots = float(
                match.group(1)
            )

            return {
                "knots": knots,
                "kmph": round(
                    knots * 1.852,
                    1
                )
            }

    return None


def extract_gust(text):

    match = re.search(
        r"gusting\s+to\s+"
        r"(\d+(?:\.\d+)?)\s*kt",
        text,
        re.IGNORECASE
    )

    if not match:

        return None

    knots = float(
        match.group(1)
    )

    return {
        "knots": knots,
        "kmph": round(
            knots * 1.852,
            1
        )
    }


def extract_development_forecast(text):

    patterns = [

        r"concentrate\s+into\s+a\s+"
        r"([A-Za-z ]+?)\s+"
        r"during\s+next\s+(\d+)\s*hours?",

        r"likely\s+to\s+concentrate\s+into\s+a\s+"
        r"([A-Za-z ]+?)\s+"
        r"during\s+next\s+(\d+)\s*hours?"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            return {

                "development":
                    clean_text(
                        match.group(1)
                    ),

                "time_window_hours":
                    int(
                        match.group(2)
                    )
            }

    return None


def extract_cyclogenesis_probability(
    text
):

    marker = re.search(
        r"\*PROBABILITY OF CYCLOGENESIS.*?"
        r"(?=\*NOTE:)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not marker:

        return {}

    section = marker.group(0)

    values = re.findall(
        r"\b(NIL|LOW|MODERATE|MOD|HIGH)\b",
        section,
        re.IGNORECASE
    )

    periods = [
        "12h",
        "12-36h",
        "36-60h",
        "60-84h",
        "84-108h",
        "108-132h",
        "132-156h"
    ]

    result = {}

    for index, period in enumerate(
        periods
    ):

        if index >= len(values):

            break

        result[period] = (
            values[index].upper()
        )

    return result


# ============================================================
# IMPORTANT:
# ONLY THESE ARE REAL SYSTEM STARTS
# ============================================================

SYSTEM_START_PATTERN = re.compile(
    r"\(([a-z])\)\s*"
    r"("
    r"Well\s+Marked\s+low\s+pressure\s+area"
    r"|"
    r"Low\s+pressure\s+area"
    r"|"
    r"Deep\s+Depression"
    r"|"
    r"Depression"
    r"|"
    r"Very\s+Severe\s+Cyclonic\s+Storm"
    r"|"
    r"Extremely\s+Severe\s+Cyclonic\s+Storm"
    r"|"
    r"Severe\s+Cyclonic\s+Storm"
    r"|"
    r"Cyclonic\s+Storm"
    r")",
    re.IGNORECASE
)


def extract_real_rsmc_system_sections(
    text
):

    cleaned = clean_text(
        text
    )

    matches = list(
        SYSTEM_START_PATTERN.finditer(
            cleaned
        )
    )

    sections = []

    for index, match in enumerate(
        matches
    ):

        start = match.start()

        if index + 1 < len(matches):

            end = matches[
                index + 1
            ].start()

        else:

            end = len(
                cleaned
            )

        section = cleaned[
            start:end
        ]

        sections.append({

            "system_id":
                match.group(1).lower(),

            "system_type":
                match.group(2),

            "section":
                section
        })

    return sections


def extract_system_description(
    section
):

    match = re.match(
        r"\([a-z]\)\s*(.*?)(?:\bat\b|\blay\b|\bover\b)",
        section,
        re.IGNORECASE
    )

    if match:

        return clean_text(
            match.group(1)
        )

    return clean_text(
        section[:250]
    )

def parse_rsmc_bulletin(pdf_content):
    """
    Parse the official RSMC New Delhi Tropical Weather Outlook.

    The RSMC PDF is downloaded as bytes. This function accepts those
    bytes, extracts the PDF text, and parses the active system and
    its forecast track.

    Current RSMC format example:

    Sub: Deep Depression over north Andaman Sea & adjoining Myanmar coast

    28.09.26/0600 16.4/97.3 50-60 gusting 70 Deep Depression
    28.09.26/1200 16.9/97.1 55-65 gusting 75 Deep Depression
    """

    if not pdf_content:
        return {
            "systems": [],
            "source": "RSMC New Delhi",
            "source_type": "official_rsmc"
        }

    # Accept either raw PDF bytes or already extracted text.
    if isinstance(pdf_content, (bytes, bytearray)):
        text = extract_pdf_text(pdf_content)
    else:
        text = str(pdf_content)

    if not text.strip():
        return {
            "systems": [],
            "source": "RSMC New Delhi",
            "source_type": "official_rsmc"
        }

    normalized_text = text.replace("\r", "\n")
    normalized_text = re.sub(
        r"[ \t]+",
        " ",
        normalized_text
    )

    # ---------------------------------------------------------
    # Find active system heading
    # ---------------------------------------------------------

    sub_match = re.search(
        r"Sub:\s*(.+?)(?=\n|The\s+)",
        normalized_text,
        flags=re.IGNORECASE
    )

    if not sub_match:
        # Fallback: the current bulletin can occasionally have
        # the heading immediately followed by paragraph text.
        sub_match = re.search(
            r"Sub:\s*(.+?)(?=\s+The\s+)",
            normalized_text,
            flags=re.IGNORECASE
        )

    if not sub_match:
        print("No RSMC 'Sub:' system heading found.")
        return {
            "systems": [],
            "source": "RSMC New Delhi",
            "source_type": "official_rsmc"
        }

    system_title = clean_text(
        sub_match.group(1)
    )

    print("\nRSMC system heading:")
    print(system_title)

    # ---------------------------------------------------------
    # Determine current category
    # ---------------------------------------------------------

    title_upper = system_title.upper()

    category = "UNKNOWN"

    category_patterns = [
        ("SUPER CYCLONIC STORM", "Super Cyclonic Storm"),
        (
            "EXTREMELY SEVERE CYCLONIC STORM",
            "Extremely Severe Cyclonic Storm"
        ),
        (
            "VERY SEVERE CYCLONIC STORM",
            "Very Severe Cyclonic Storm"
        ),
        (
            "SEVERE CYCLONIC STORM",
            "Severe Cyclonic Storm"
        ),
        ("CYCLONIC STORM", "Cyclonic Storm"),
        ("DEEP DEPRESSION", "Deep Depression"),
        ("DEPRESSION", "Depression"),
        (
            "WELL MARKED LOW PRESSURE AREA",
            "Well Marked Low Pressure Area"
        ),
        ("LOW PRESSURE AREA", "Low Pressure Area")
    ]

    for keyword, label in category_patterns:
        if keyword in title_upper:
            category = label
            break

    # ---------------------------------------------------------
    # Forecast track table
    # ---------------------------------------------------------

    track = []

    table_pattern = re.compile(
        r"""
        (?P<date>\d{2}\.\d{2}\.\d{2})
        /
        (?P<time>\d{4})
        \s+
        (?P<latitude>\d+(?:\.\d+))
        /
        (?P<longitude>\d+(?:\.\d+))
        \s+
        (?P<wind>\d+(?:-\d+)?(?:\s+gusting\s+\d+)?)
        \s+
        (?P<category>
            Super\ Cyclonic\ Storm |
            Extremely\ Severe\ Cyclonic\ Storm |
            Very\ Severe\ Cyclonic\ Storm |
            Severe\ Cyclonic\ Storm |
            Cyclonic\ Storm |
            Deep\ Depression |
            Depression |
            Well\ Marked\ Low\ Pressure\ Area |
            Low\ Pressure\ Area
        )
        """,
        flags=re.IGNORECASE | re.VERBOSE
    )

    for match in table_pattern.finditer(normalized_text):
        date_value = match.group("date")
        time_value = match.group("time")

        latitude = float(
            match.group("latitude")
        )

        longitude = float(
            match.group("longitude")
        )

        wind_text = match.group("wind").strip()

        category_value = clean_text(
            match.group("category")
        )

        try:
            dt = datetime.strptime(
                f"{date_value}/{time_value}",
                "%d.%m.%y/%H%M"
            )
            timestamp = dt.isoformat()

        except ValueError:
            timestamp = (
                f"{date_value}/{time_value}"
            )

        # Take the midpoint of a stated wind range.
        wind_match = re.search(
            r"(\d+)(?:-(\d+))?",
            wind_text
        )

        wind_kmph = None

        if wind_match:
            wind_low = float(
                wind_match.group(1)
            )

            wind_high = (
                float(wind_match.group(2))
                if wind_match.group(2)
                else wind_low
            )

            wind_kmph = round(
                (wind_low + wind_high) / 2,
                1
            )

        gust_match = re.search(
            r"gusting\s+(\d+)",
            wind_text,
            flags=re.IGNORECASE
        )

        gust_kmph = (
            float(gust_match.group(1))
            if gust_match
            else None
        )

        track.append({
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "wind_kmph": wind_kmph,
            "gust_kmph": gust_kmph,
            "category": category_value
        })

    # ---------------------------------------------------------
    # Current position
    # ---------------------------------------------------------

    current_latitude = None
    current_longitude = None

    current_position_match = re.search(
        r"lay\s+centred"
        r".{0,300}?"
        r"near\s+latitude\s+"
        r"(\d+(?:\.\d+)?)"
        r"[°]?\s*N"
        r"\s+and\s+longitude\s+"
        r"(\d+(?:\.\d+)?)"
        r"[°]?\s*E",
        normalized_text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if current_position_match:
        current_latitude = float(
            current_position_match.group(1)
        )

        current_longitude = float(
            current_position_match.group(2)
        )

    # Fallback to first forecast point.
    if (
        current_latitude is None
        and track
    ):
        current_latitude = track[0]["latitude"]
        current_longitude = track[0]["longitude"]

    # ---------------------------------------------------------
    # Current pressure and wind
    # ---------------------------------------------------------

    central_pressure = extract_pressure(
        normalized_text
    )

    current_wind = extract_wind(
        normalized_text
    )

    current_gust = extract_gust(
        normalized_text
    )

    if current_wind is None and track:
        current_track_wind = track[0].get(
            "wind_kmph"
        )

        if current_track_wind is not None:
            current_wind = {
                "knots": round(
                    current_track_wind / 1.852,
                    1
                ),
                "kmph": current_track_wind
            }

    # ---------------------------------------------------------
    # Movement / other information
    # ---------------------------------------------------------

    movement = extract_movement(
        normalized_text
    )

    development_forecast = (
        extract_development_forecast(
            normalized_text
        )
    )

    cyclogenesis_probability = (
        extract_cyclogenesis_probability(
            normalized_text
        )
    )

    # Description is the text around the Sub: heading.
    description_start = sub_match.start()

    description_end = (
        normalized_text.find(
            "The forecast track",
            description_start
        )
    )

    if description_end == -1:
        description_end = min(
            description_start + 1500,
            len(normalized_text)
        )

    description = clean_text(
        normalized_text[
            description_start:description_end
        ]
    )

    coordinates = []

    if (
        current_latitude is not None
        and current_longitude is not None
    ):
        coordinates.append({
            "latitude": current_latitude,
            "longitude": current_longitude
        })

    # ---------------------------------------------------------
    # Build system in the normalized structure expected by the
    # rest of this file.
    # ---------------------------------------------------------

    system = {
        "system_id": "a",
        "system_type": category,
        "description": description,
        "coordinates": coordinates,
        "movement": movement,
        "central_pressure_hpa": central_pressure,
        "maximum_wind": current_wind,
        "maximum_gust": current_gust,
        "development_forecast": development_forecast,
        "cyclogenesis_probability":
            cyclogenesis_probability,
        "name": system_title,
        "title": system_title,
        "current_latitude": current_latitude,
        "current_longitude": current_longitude,
        "track": track,
        "source": "RSMC New Delhi",
        "source_type": "official_rsmc"
    }

    print(
        "\n===== PARSED RSMC SYSTEM ====="
    )

    print(
        "Name:",
        system["name"]
    )

    print(
        "Category:",
        system["system_type"]
    )

    print(
        "Current position:",
        current_latitude,
        current_longitude
    )

    print(
        "Central pressure:",
        central_pressure
    )

    print(
        "Current wind:",
        current_wind
    )

    print(
        "Forecast points:",
        len(track)
    )

    for point in track:
        print(point)

    return {
        "systems": [system],
        "source": "RSMC New Delhi",
        "source_type": "official_rsmc"
    }


# ============================================================
# TRACK ARCHIVE
# ============================================================

def find_track_images():

    print(
        "\n===== IMD TRACK ARCHIVE ====="
    )

    response = fetch_url(
        ARCHIVE_URL,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    tracks = []

    for row in soup.find_all(
        "tr"
    ):

        cells = row.find_all(
            "td"
        )

        if len(cells) < 4:

            continue

        title = cells[1].get_text(
            " ",
            strip=True
        )

        issue_time = cells[2].get_text(
            " ",
            strip=True
        )

        link = cells[3].find(
            "a"
        )

        if not link:

            continue

        href = link.get(
            "href"
        )

        if not href:

            continue

        if (
            "Observed & Forecast Track"
            not in title
        ):

            continue

        tracks.append({

            "title":
                title,

            "issue_time":
                issue_time,

            "url":
                urljoin(
                    ARCHIVE_URL,
                    href
                )
        })

    print(
        "Track products found:",
        len(tracks)
    )

    for index, track in enumerate(
        tracks[:10],
        start=1
    ):

        print(
            f"{index}.",
            track["title"]
        )

        print(
            "   Issue:",
            track["issue_time"]
        )

        print(
            "   URL:",
            track["url"]
        )

    return tracks


def download_track_image(
    track,
    filename
):

    TRACK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    response = fetch_url(
        track["url"],
        timeout=30
    )

    path = (
        TRACK_DIR /
        filename
    )

    path.write_bytes(
        response.content
    )

    print(
        "\nTrack downloaded:"
    )

    print(
        "Title:",
        track["title"]
    )

    print(
        "Issue:",
        track["issue_time"]
    )

    print(
        "Saved:",
        path
    )

    print(
        "Size:",
        len(response.content)
    )

    return path


# ============================================================
# TRACK OCR VALIDATION
# ============================================================

def extract_track_image_text(
    image_path
):

    image = Image.open(
        image_path
    )

    return pytesseract.image_to_string(
        image
    )


def detect_track_region(
    text
):

    upper = text.upper()

    if "UTTAR PRADESH" in upper:

        return "UTTAR_PRADESH"

    if "ODISHA" in upper:

        return "ODISHA"

    if "ORISSA" in upper:

        return "ODISHA"

    if "ANDAMAN" in upper:

        return "ANDAMAN"

    if "MYANMAR" in upper:

        return "MYANMAR"

    if "BANGLADESH" in upper:

        return "BANGLADESH"

    if "BAY OF BENGAL" in upper:

        return "BAY_OF_BENGAL"

    if "ARABIAN SEA" in upper:

        return "ARABIAN_SEA"

    return "UNKNOWN"


def validate_track_image(
    image_path
):

    text = extract_track_image_text(
        image_path
    )

    region = detect_track_region(
        text
    )

    upper = text.upper()

    # --------------------------------------------------------
    # Clearly unrelated regions
    # --------------------------------------------------------

    rejected_regions = [

        "UTTAR PRADESH",

        "RAJASTHAN",

        "MADHYA PRADESH",

        "HARYANA",

        "PUNJAB",

        "DELHI",

        "MYANMAR",

        "BANGLADESH",

        "ANDAMAN",

        "NORTH ANDAMAN SEA",

        "ANDAMAN SEA",

        "ARABIAN SEA",

    ]

    rejected = any(
        keyword in upper
        for keyword in rejected_regions
    )

    # --------------------------------------------------------
    # Explicit Odisha reference
    # --------------------------------------------------------

    explicit_odisha = (
        "ODISHA" in upper
        or
        "ORISSA" in upper
    )

    # --------------------------------------------------------
    # Bay of Bengal context
    #
    # Bay of Bengal alone does NOT mean Odisha relevance.
    # --------------------------------------------------------

    bay_of_bengal_context = (
        "BAY OF BENGAL" in upper
    )

    # --------------------------------------------------------
    # Final decision
    #
    # We require explicit Odisha reference and reject
    # clearly unrelated regions.
    # --------------------------------------------------------

    accepted = (
        explicit_odisha
        and
        not rejected
    )

    return {

        "accepted_for_odisha":
            accepted,

        "detected_region":
            region,

        "explicit_odisha":
            explicit_odisha,

        "bay_of_bengal_context":
            bay_of_bengal_context,

        "rejected_as_unrelated":
            rejected,

        "ocr_text":
            text
    }


def find_odisha_relevant_track(
    tracks,
    max_candidates=5
):

    print(
        "\n===== SEARCHING FOR ODISHA-RELEVANT TRACK ====="
    )

    candidates_checked = []

    for index, track in enumerate(
        tracks[:max_candidates],
        start=1
    ):

        print(
            "\nTrack downloaded:"
        )

        print(
            "Title:",
            track.get("title")
        )

        print(
            "Issue:",
            track.get("issue_time")
        )

        image_url = track.get(
            "url"
        )

        if not image_url:

            print(
                "No image URL found."
            )

            continue

        image_path = (
            TRACK_DIR
            / f"candidate_{index}.png"
        )

        try:

            image_data = fetch_url(
                image_url,
                timeout=30
            ).content

            with open(
                image_path,
                "wb"
            ) as file:

                file.write(
                    image_data
                )

            print(
                "Saved:",
                image_path
            )

            print(
                "Size:",
                len(image_data)
            )

        except requests.exceptions.RequestException as error:

            print(
                "Track download failed:",
                error
            )

            continue

        except Exception as error:

            print(
                "Track download error:",
                error
            )

            continue

        validation = validate_track_image(
            image_path
        )

        detected_region = validation.get(
            "detected_region",
            "UNKNOWN"
        )

        explicit_odisha = validation.get(
            "explicit_odisha",
            False
        )

        bay_of_bengal_context = validation.get(
            "bay_of_bengal_context",
            False
        )

        rejected_as_unrelated = validation.get(
            "rejected_as_unrelated",
            False
        )

        accepted_for_odisha = validation.get(
            "accepted_for_odisha",
            False
        )

        print(
            "\nCandidate:",
            index
        )

        print(
            "Detected region:",
            detected_region
        )

        print(
            "Explicit Odisha:",
            explicit_odisha
        )

        print(
            "Bay of Bengal context:",
            bay_of_bengal_context
        )

        print(
            "Rejected as unrelated:",
            rejected_as_unrelated
        )

        print(
            "Accepted for Odisha:",
            accepted_for_odisha
        )

        candidates_checked.append({

            "candidate":
                index,

            "title":
                track.get(
                    "title"
                ),

            "issue_time":
                track.get(
                    "issue_time"
                ),

            "image_url":
                image_url,

            "image_path":
                str(
                    image_path
                ),

            "detected_region":
                detected_region,

            "explicit_odisha":
                explicit_odisha,

            "bay_of_bengal_context":
                bay_of_bengal_context,

            "rejected_as_unrelated":
                rejected_as_unrelated,

            "accepted_for_odisha":
                accepted_for_odisha,

            "ocr_text":
                validation.get(
                    "ocr_text",
                    ""
                )
        })

        if accepted_for_odisha:

            print(
                "\nODISHA-RELEVANT TRACK FOUND"
            )

            return {

                "found":
                    True,

                "track":
                    track,

                "validation":
                    validation,

                "candidates_checked":
                    candidates_checked
            }

    print(
        "\nNo Odisha-relevant track found."
    )

    return {

        "found":
            False,

        "track":
            None,

        "validation":
            None,

        "candidates_checked":
            candidates_checked,

        "reason":
            (
                "No track product among the "
                f"first {max_candidates} candidates "
                "was explicitly identified as relevant "
                "to Odisha."
            )
    }


# ============================================================
# ODISHA GEOGRAPHY
# ============================================================

def point_inside_odisha(
    latitude,
    longitude
):

    if not ODISHA_GEOJSON.exists():

        raise FileNotFoundError(
            f"Odisha GeoJSON not found: "
            f"{ODISHA_GEOJSON}"
        )

    odisha = gpd.read_file(
        ODISHA_GEOJSON
    )

    point = gpd.GeoDataFrame(
        geometry=[
            Point(
                longitude,
                latitude
            )
        ],
        crs="EPSG:4326"
    )

    point = point.to_crs(
        odisha.crs
    )

    return bool(
        odisha.geometry.contains(
            point.geometry.iloc[0]
        ).any()
    )

def check_odisha_relevance(
    system
):
    """
    Determine whether the RSMC system is relevant to Odisha.

    Priority:
    1. Check every parsed forecast point against Odisha geometry.
    2. Check whether the forecast track comes within 100 km of Odisha.
    3. Check explicit Odisha/Orissa wording.
    4. Reject clearly unrelated regions.

    Bay of Bengal alone is never treated as sufficient evidence.
    """

    # --------------------------------------------------------
    # Forecast-track geographic check
    # --------------------------------------------------------

    track = system.get(
        "track",
        []
    )

    for point in track:

        latitude = point.get(
            "latitude"
        )

        longitude = point.get(
            "longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            continue

        if point_inside_odisha(
            latitude,
            longitude
        ):
            return True

    # --------------------------------------------------------
    # Current coordinate check
    # --------------------------------------------------------

    current_latitude = system.get(
        "current_latitude"
    )

    current_longitude = system.get(
        "current_longitude"
    )

    if (
        current_latitude is not None
        and current_longitude is not None
        and point_inside_odisha(
            current_latitude,
            current_longitude
        )
    ):
        return True

    # --------------------------------------------------------
    # Text-based check
    # --------------------------------------------------------

    description = system.get(
        "description",
        ""
    )

    title = system.get(
        "name",
        ""
    )

    text = (
        f"{title} {description}"
    ).upper()

    if "ODISHA" in text:
        return True

    if "ORISSA" in text:
        return True

    # --------------------------------------------------------
    # Explicitly unrelated regions
    # --------------------------------------------------------

    unrelated_regions = [
        "UTTAR PRADESH",
        "CENTRAL UTTAR PRADESH",
        "NORTH ANDAMAN SEA",
        "ANDAMAN SEA",
        "MYANMAR COAST",
        "MYANMAR",
        "BANGLADESH",
        "ARABIAN SEA",
        "RAJASTHAN",
        "MADHYA PRADESH",
        "HARYANA",
        "PUNJAB",
        "DELHI"
    ]

    for region in unrelated_regions:

        if region in text:
            return False

    # Bay of Bengal alone is not enough.
    return False


# ============================================================
# BUILD CURRENT SYSTEM
# ============================================================

def build_current_system(
    rsmc_system
):

    wind = rsmc_system.get(
        "maximum_wind"
    )

    gust = rsmc_system.get(
        "maximum_gust"
    )

    coordinates = (
        rsmc_system.get(
            "coordinates",
            []
        )
    )

    latitude = None
    longitude = None

    if coordinates:

        latitude = coordinates[
            0
        ]["latitude"]

        longitude = coordinates[
            0
        ]["longitude"]

    return {

        "source":
            "IMD RSMC Bulletin",

        "system_id":
            rsmc_system.get(
                "system_id"
            ),

        "system_type":
            rsmc_system.get(
                "system_type"
            ),

        "description":
            rsmc_system.get(
                "description"
            ),

        "latitude":
            latitude,

        "longitude":
            longitude,

        "coordinates":
            coordinates,

        "movement":
            rsmc_system.get(
                "movement"
            ),

        "central_pressure_hpa":
            rsmc_system.get(
                "central_pressure_hpa"
            ),

        "maximum_wind_kmph":
            (
                wind["kmph"]
                if wind
                else None
            ),

        "maximum_wind_kt":
            (
                wind["knots"]
                if wind
                else None
            ),

        "maximum_gust_kmph":
            (
                gust["kmph"]
                if gust
                else None
            ),

        "maximum_gust_kt":
            (
                gust["knots"]
                if gust
                else None
            ),

        "development_forecast":
            rsmc_system.get(
                "development_forecast"
            ),

        "cyclogenesis_probability":
            rsmc_system.get(
                "cyclogenesis_probability"
            ),

        "track":
            rsmc_system.get(
                "track",
                []
            ),

        "name":
            rsmc_system.get(
                "name"
            ),

        "title":
            rsmc_system.get(
                "title"
            ),

        "odisha_relevant":
            check_odisha_relevance(
                rsmc_system
            )
    }


# ============================================================
# MAIN INGESTION
# ============================================================

def get_current_imd_data():

    print(
        "\n" + "=" * 70
    )

    print(
        "LIVE IMD CYCLONE INGESTION"
    )

    print(
        "=" * 70
    )

    homepage = fetch_imd_homepage()

    links = get_current_bulletin_links(
        homepage
    )

    print(
        "\n===== CURRENT IMD BULLETINS ====="
    )

    for link in links:

        print(
            link["type"]
        )

        print(
            link["url"]
        )

        print(
            "-" * 70
        )

    national_link = get_bulletin_by_type(
        links,
        "National Bulletin"
    )

    rsmc_link = get_bulletin_by_type(
        links,
        "RSMC Bulletin"
    )

    national_data = {}
    rsmc_data = {}

    # --------------------------------------------------------
    # NATIONAL
    # --------------------------------------------------------

    if national_link:

        print(
            "\n===== NATIONAL BULLETIN ====="
        )

        national_pdf = download_bulletin(
            national_link["url"]
        )

        national_data = (
            parse_national_bulletin(
                national_pdf
            )
        )

        print(
            "National system:",
            national_data.get(
                "system_type"
            )
        )

        print(
            "National coordinates:",
            national_data.get(
                "coordinates"
            )
        )

    # --------------------------------------------------------
    # RSMC
    # --------------------------------------------------------

    if rsmc_link:

        print(
            "\n===== RSMC BULLETIN ====="
        )

        rsmc_pdf = download_bulletin(
            rsmc_link["url"]
        )

        rsmc_data = (
            parse_rsmc_bulletin(
                rsmc_pdf
            )
        )

        print(
            "\n===== REAL RSMC SYSTEMS ====="
        )

        for system in rsmc_data[
            "systems"
        ]:

            print(
                "\nSystem:",
                system[
                    "system_id"
                ]
            )

            print(
                "Type:",
                system[
                    "system_type"
                ]
            )

            print(
                "Description:",
                system[
                    "description"
                ][:300]
            )

            print(
                "Coordinates:",
                system[
                    "coordinates"
                ]
            )

            print(
                "Movement:",
                system[
                    "movement"
                ]
            )

            print(
                "Pressure:",
                system[
                    "central_pressure_hpa"
                ]
            )

            print(
                "Wind:",
                system[
                    "maximum_wind"
                ]
            )

            print(
                "Gust:",
                system[
                    "maximum_gust"
                ]
            )

            print(
                "Development:",
                system[
                    "development_forecast"
                ]
            )

            print(
                "Cyclogenesis:",
                system[
                    "cyclogenesis_probability"
                ]
            )

            print(
                "-" * 70
            )

    # --------------------------------------------------------
    # TRACKS
    # --------------------------------------------------------

    tracks = find_track_images()

    track_result = None

    if tracks:

        track_result = (
            find_odisha_relevant_track(
                tracks,
                max_candidates=5
            )
        )

    # --------------------------------------------------------
    # BUILD SYSTEMS
    # --------------------------------------------------------

    current_systems = []

    for system in rsmc_data.get(
        "systems",
        []
    ):

        current_systems.append(
            build_current_system(
                system
            )
        )

    odisha_systems = [

        system

        for system in current_systems

        if system[
            "odisha_relevant"
        ]
    ]

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    result = {

        "source":
            "IMD RSMC New Delhi",

        "project_region":
            "Odisha",

        "national_bulletin":
            national_data,

        "rsmc_bulletin":
            rsmc_data,

        "current_systems":
            current_systems,

        "odisha_relevant_systems":
            odisha_systems,

        "track":
            (
                {
                    "found": True,

                    "title":
                        track_result[
                            "track"
                        ]["title"],

                    "issue_time":
                        track_result[
                            "track"
                        ]["issue_time"],

                    "url":
                        track_result[
                            "track"
                        ]["url"],

                    "path":
                        str(
                            TRACK_DIR
                            / "selected_odisha_track.png"
                        ),

                    "validation":
                        track_result[
                            "validation"
                        ]
                }

                if (
                    track_result
                    and
                    track_result.get("found")
                    and
                    track_result.get("track")
                )

                else
                {
                    "found": False,

                    "message":
                        "No Odisha-relevant "
                        "track found.",

                    "candidates_checked":
                        (
                            track_result.get(
                                "candidates_checked",
                                []
                            )
                            if track_result
                            else []
                        )
                }
            ),

        "odisha_status":
            (
                "ACTIVE_SYSTEM"

                if odisha_systems

                else
                "NO_CURRENT_ODISHA_SYSTEM"
            )
    }

    return result

# ============================================================
# SAVE NORMALIZED CURRENT DATA
# ============================================================

CURRENT_DATA_PATH = Path(
    "data/processed/current_cyclone.json"
)


def save_current_data(data):

    import json

    CURRENT_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        CURRENT_DATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "\n===== CURRENT DATA SAVED ====="
    )

    print(
        "File:",
        CURRENT_DATA_PATH
    )

    return CURRENT_DATA_PATH

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("LIVE IMD CYCLONE INGESTION")
    print("=" * 70)

    data = get_current_imd_data()

    save_current_data(data)

    print("\n" + "=" * 70)
    print("ODISHA CYCLONE STATUS")
    print("=" * 70)

    print(
        "Status:",
        data.get("odisha_status")
    )

    print(
        "Odisha systems:",
        len(
            data.get(
                "odisha_relevant_systems",
                []
            )
        )
    )

    track = data.get(
        "track",
        {}
    )

    print(
        "Track found:",
        track.get("found")
    )

    if data.get(
        "odisha_relevant_systems"
    ):

        print(
            "\nOdisha systems detected:"
        )

        for system in data[
            "odisha_relevant_systems"
        ]:

            print(
                system.get(
                    "system_type"
                )
            )

    else:

        print(
            "\nNo current Odisha cyclone."
        )

        print(
            "Risk engine will not be triggered."
        )