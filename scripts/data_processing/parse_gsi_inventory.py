import os
import re
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = "data/historical/GSI_landslide_inventory.txt"
OUTPUT_FILE = "data/historical/GSI_landslide_inventory.csv"
FAILED_FILE = "data/historical/GSI_failed_records.txt"


# ============================================================
# CHECK INPUT FILE
# ============================================================

if not os.path.exists(INPUT_FILE):
    print("ERROR: Input file not found.")
    print(f"Expected: {INPUT_FILE}")
    raise SystemExit


print("Reading GSI inventory text...")

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    text = file.read()

print(f"Characters loaded: {len(text):,}")
print()


# ============================================================
# NORMALIZE LINE BREAKS
# ============================================================

text = text.replace("\r\n", "\n").replace("\r", "\n")

lines = text.split("\n")


# ============================================================
# RECORD DETECTION
#
# IMPORTANT:
# Records are identified by the leading serial number.
# We do NOT depend on Slide_No starting with AS/ASM.
# ============================================================

print("Detecting GSI records...")

records = []

current_record = []
current_sl_no = None


for line in lines:

    stripped = line.strip()

    if not stripped:
        continue

    # Detect a line beginning with a serial number.
    match = re.match(r"^(\d+)\s+(.*)$", stripped)

    if match:

        possible_sl_no = int(match.group(1))

        # Start a new record only when the serial number
        # is different from the current record.
        if current_record and possible_sl_no != current_sl_no:

            records.append(" ".join(current_record))
            current_record = []

        if not current_record:
            current_sl_no = possible_sl_no

        current_record.append(stripped)

    else:

        # Continuation line
        if current_record:
            current_record.append(stripped)


# Add final record
if current_record:
    records.append(" ".join(current_record))


print(f"Raw records detected: {len(records)}")
print()


# ============================================================
# COORDINATE EXTRACTION
#
# Latitude:
#   6 to 38 degrees
#
# Longitude:
#   68 to 98 degrees
#
# We collect ALL valid coordinate pairs and select the pair
# closest to the end of the record.
#
# This prevents road numbers such as NH-44 from being mistaken
# for latitude.
# ============================================================

coordinate_pattern = re.compile(
    r"(?<![\d.])"
    r"(\d{1,2}(?:\.\d+)?)"
    r"\s+"
    r"(\d{1,3}(?:\.\d+)?)"
    r"(?![\d.])"
)


def find_coordinates(record):

    candidates = []

    for match in coordinate_pattern.finditer(record):

        latitude = float(match.group(1))
        longitude = float(match.group(2))

        if 6 <= latitude <= 38 and 68 <= longitude <= 98:

            candidates.append(
                (
                    match.start(),
                    latitude,
                    longitude
                )
            )

    if not candidates:
        return None, None

    # Use the LAST valid coordinate pair in this record.
    _, latitude, longitude = candidates[-1]

    return latitude, longitude


# ============================================================
# STATE LIST
# ============================================================

states = [
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
    "Uttarakhand",
    "West Bengal",
    "Bihar",
    "Jharkhand",
    "Odisha",
    "Chhattisgarh",
    "Madhya Pradesh",
    "Rajasthan",
    "Gujarat",
    "Maharashtra",
    "Goa",
    "Karnataka",
    "Kerala",
    "Tamil Nadu",
    "Andhra Pradesh",
    "Telangana",
    "Uttar Pradesh",
    "Himachal Pradesh",
    "Punjab",
    "Haryana",
    "Jammu and Kashmir",
    "Ladakh",
    "Delhi",
]


# ============================================================
# MOVEMENT TYPES
# ============================================================

movement_patterns = [
    "Rock cum Debris Slide",
    "Rock-cum- debris Falls",
    "Rock-cum-Debris Falls",
    "Rock cum debris Slide",
    "Rock cum debris slide",
    "Rock + Debris Slide + fall",
    "Rock & Debris Slide",
    "Rock & fall",
    "Earth Shallow rotational",
    "Debris Toppled",
    "Soil Subsidence",
    "Debris Subsidence",
    "Debris Flows",
    "Debris Flow",
    "Debris Fall",
    "debris Fall",
    "debris slide",
    "Debris Slide",
    "Earth Slide",
    "Soil Slide",
    "Rock Slide",
    "Rock Fall",
    "Earth Flow",
    "Creep",
    "Subsidence",
]


# ============================================================
# HISTORY PATTERNS
# ============================================================

history_pattern = re.compile(
    r"("
    r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
    r"(?:,\s*[^,]*)?"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
    r"|"
    r"\d{4}"
    r")",
    re.IGNORECASE
)


# ============================================================
# FIND STATE
# ============================================================

def find_state(record):

    for state in states:

        if re.search(
            rf"\b{re.escape(state)}\b",
            record,
            re.IGNORECASE
        ):
            return state

    return None


# ============================================================
# FIND DISTRICT
#
# District is the text immediately after the state and before
# the next coordinate pair.
# ============================================================

def find_district(record, state, latitude, longitude):

    if not state:
        return None

    state_match = re.search(
        rf"\b{re.escape(state)}\b",
        record,
        re.IGNORECASE
    )

    if not state_match:
        return None

    after_state = record[state_match.end():]

    # Remove coordinate and everything after it.
    coordinate_match = re.search(
        rf"\b{re.escape(str(latitude))}\b\s+\b{re.escape(str(longitude))}\b",
        after_state
    )

    if coordinate_match:
        before_coordinates = after_state[:coordinate_match.start()]
    else:
        before_coordinates = after_state

    before_coordinates = before_coordinates.strip()

    if not before_coordinates:
        return None

    # Usually the district is the first meaningful field
    # after the state.
    words = before_coordinates.split()

    if not words:
        return None

    # Common district names with multiple words.
    multiword_districts = [
        "West Karbi Anglong",
        "Karbi Anglong",
        "Dima Hasao",
        "South West Garo Hills",
        "West Jaintia Hills",
        "East Jaintia Hills",
        "Ri-Bhoi",
        "Kamrup (Metro)",
        "Kamrup (Rural)",
    ]

    for district in multiword_districts:

        if before_coordinates.lower().startswith(
            district.lower()
        ):
            return district

    return words[0]


# ============================================================
# FIND MOVEMENT TYPE
# ============================================================

def find_movement_type(record):

    # Check longer patterns first.
    patterns = sorted(
        movement_patterns,
        key=len,
        reverse=True
    )

    for movement in patterns:

        match = re.search(
            re.escape(movement),
            record,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return None


# ============================================================
# FIND HISTORY
# ============================================================

def find_history(record, movement_type):

    if not movement_type:
        return None

    movement_match = re.search(
        re.escape(movement_type),
        record,
        re.IGNORECASE
    )

    if not movement_match:
        return None

    after_movement = record[movement_match.end():].strip()

    if not after_movement:
        return None

    if after_movement.upper().startswith("NA"):
        return None

    if after_movement.upper().startswith("NIL"):
        return None

    history_match = history_pattern.search(
        after_movement
    )

    if history_match:
        return history_match.group(0).strip()

    return after_movement if after_movement else None


# ============================================================
# FIND DESCRIPTION
#
# Description is kept conservatively.
# We do not invent missing descriptions.
# ============================================================

def find_description(
    record,
    state,
    latitude,
    longitude,
    movement_type
):

    if not state:
        return None

    state_match = re.search(
        rf"\b{re.escape(state)}\b",
        record,
        re.IGNORECASE
    )

    if not state_match:
        return None

    after_state = record[state_match.end():].strip()

    # Remove everything from coordinates onward.
    coordinate_match = re.search(
        r"\d{1,2}(?:\.\d+)?\s+\d{1,3}(?:\.\d+)?",
        after_state
    )

    if coordinate_match:
        before_coordinates = (
            after_state[:coordinate_match.start()]
        ).strip()
    else:
        before_coordinates = after_state

    if not before_coordinates:
        return None

    # Remove obvious district name.
    district_words = before_coordinates.split()

    if len(district_words) <= 1:
        return None

    # For descriptions, preserve the original text.
    return before_coordinates


# ============================================================
# PARSE RECORDS
# ============================================================

parsed_records = []
failed_records = []

suspicious_coordinates = []


for index, record in enumerate(records, start=1):

    # --------------------------------------------------------
    # SERIAL NUMBER
    # --------------------------------------------------------

    sl_match = re.match(
        r"^(\d+)",
        record
    )

    if not sl_match:
        failed_records.append(record)
        continue

    sl_no = int(sl_match.group(1))

    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

    latitude, longitude = find_coordinates(record)

    if latitude is None or longitude is None:

        failed_records.append(record)
        continue

    # --------------------------------------------------------
    # VALIDATE COORDINATES
    # --------------------------------------------------------

    if not (
        6 <= latitude <= 38
        and
        68 <= longitude <= 98
    ):

        suspicious_coordinates.append(
            (
                sl_no,
                latitude,
                longitude,
                record
            )
        )

        continue

    # --------------------------------------------------------
    # SLIDE NUMBER
    # --------------------------------------------------------

    slide_match = re.match(
        r"^\d+\s+(\S+)",
        record
    )

    slide_no = (
        slide_match.group(1)
        if slide_match
        else None
    )

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    state = find_state(record)

    if not state:
        failed_records.append(record)
        continue

    # --------------------------------------------------------
    # DISTRICT
    # --------------------------------------------------------

    district = find_district(
        record,
        state,
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # MOVEMENT TYPE
    # --------------------------------------------------------

    movement_type = find_movement_type(record)

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history = find_history(
        record,
        movement_type
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = find_description(
        record,
        state,
        latitude,
        longitude,
        movement_type
    )

    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    parsed_records.append(
        {
            "sl_no": sl_no,
            "slide_no": slide_no,
            "state": state,
            "district": district,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "material": None,
            "movement_type": movement_type,
            "history": history,
            "raw_record": record,
        }
    )

    if index % 500 == 0:
        print(
            f"Processed {index}/{len(records)}"
        )


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(parsed_records)


# ============================================================
# SAVE CSV
# ============================================================

os.makedirs(
    "data/historical",
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# SAVE FAILED RECORDS
# ============================================================

with open(
    FAILED_FILE,
    "w",
    encoding="utf-8"
) as file:

    for record in failed_records:
        file.write(record + "\n")


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 55)
print("GSI PARSING COMPLETED")
print("=" * 55)

print(
    f"Raw records detected       : {len(records)}"
)

print(
    f"Successfully parsed        : {len(parsed_records)}"
)

print(
    f"Failed records             : {len(failed_records)}"
)

print(
    f"Suspicious coordinates     : {len(suspicious_coordinates)}"
)

print(
    f"CSV saved to               : {OUTPUT_FILE}"
)

print("=" * 55)


# ============================================================
# STATE DISTRIBUTION
# ============================================================

if not df.empty:

    print()
    print("State distribution:")
    print("-" * 46)
    print(
        df["state"]
        .value_counts()
        .to_string()
    )


# ============================================================
# MOVEMENT TYPE DISTRIBUTION
# ============================================================

if not df.empty:

    print()
    print("Movement type distribution:")
    print("-" * 46)
    print(
        df["movement_type"]
        .value_counts(dropna=False)
        .to_string()
    )


# ============================================================
# COORDINATE VALIDATION
# ============================================================

if not df.empty:

    bad_coordinates = df[
        (df["latitude"] < 6)
        |
        (df["latitude"] > 38)
        |
        (df["longitude"] < 68)
        |
        (df["longitude"] > 98)
    ]

    print()

    if len(bad_coordinates) == 0:
        print("Coordinate validation passed.")
    else:
        print(
            "WARNING: Invalid coordinates detected:",
            len(bad_coordinates)
        )


# ============================================================
# SHOW FIRST 5
# ============================================================

if not df.empty:

    print()
    print("First 5 parsed records:")
    print("-" * 46)

    print(
        df[
            [
                "sl_no",
                "slide_no",
                "state",
                "district",
                "latitude",
                "longitude",
                "movement_type",
                "history",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


# ============================================================
# FAILED RECORD WARNING
# ============================================================

if failed_records:

    print()
    print(
        f"WARNING: {len(failed_records)} records could not be parsed."
    )

    print(
        f"See: {FAILED_FILE}"
    )

print()