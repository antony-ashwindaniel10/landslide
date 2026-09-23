import os
import time
import earthaccess


DATE_FILE = "data/weather/failed_imerg_dates.txt"
OUTPUT_DIR = "data/weather"


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(DATE_FILE):
    print("ERROR: Failed-date file not found.")
    print(f"Expected: {DATE_FILE}")
    raise SystemExit


os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# READ FAILED DATES
# ============================================================

with open(DATE_FILE, "r", encoding="utf-8") as file:
    dates = [
        line.strip()
        for line in file
        if line.strip()
    ]

dates = sorted(set(dates))


print("=" * 60)
print("NASA IMERG FAILED-DATE RETRY")
print("=" * 60)
print()
print(f"Dates to retry: {len(dates)}")
print()


# ============================================================
# LOGIN
# ============================================================

print("Logging into NASA Earthdata...")

earthaccess.login()

print("Earthdata authentication successful.")
print()


# ============================================================
# RETRY DOWNLOADS
# ============================================================

downloaded = 0
already_exists = 0
failed = 0

still_failed = []


for index, date in enumerate(dates, start=1):

    print("-" * 60)
    print(f"[{index}/{len(dates)}] Processing: {date}")

    expected_filename = (
        f"3B-DAY.MS.MRG.3IMERG."
        f"{date.replace('-', '')}"
        f"-S000000-E235959.V07B.nc4"
    )

    expected_path = os.path.join(
        OUTPUT_DIR,
        expected_filename
    )

    # --------------------------------------------------------
    # Check whether already downloaded
    # --------------------------------------------------------

    if os.path.exists(expected_path):

        print("Already exists - skipping.")

        already_exists += 1

        continue


    # --------------------------------------------------------
    # Search NASA
    # --------------------------------------------------------

    try:

        results = earthaccess.search_data(
            short_name="GPM_3IMERGDF",
            version="07",
            temporal=(
                f"{date}T00:00:00",
                f"{date}T23:59:59"
            ),
            count=1
        )

    except Exception as error:

        print(f"Search failed: {error}")

        failed += 1
        still_failed.append(date)

        time.sleep(3)

        continue


    # --------------------------------------------------------
    # No result
    # --------------------------------------------------------

    if not results:

        print("No IMERG file found.")

        failed += 1
        still_failed.append(date)

        time.sleep(2)

        continue


    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    try:

        files = earthaccess.download(
            results[0],
            local_path=OUTPUT_DIR
        )

        if files:

            print("Download successful.")

            downloaded += 1

        else:

            print("Download returned no files.")

            failed += 1
            still_failed.append(date)

    except Exception as error:

        print(f"Download failed: {error}")

        failed += 1
        still_failed.append(date)


    # Small delay between requests
    time.sleep(2)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("RETRY COMPLETED")
print("=" * 60)

print(f"Dates retried     : {len(dates)}")
print(f"Downloaded        : {downloaded}")
print(f"Already existed   : {already_exists}")
print(f"Failed again      : {failed}")
print()


# ============================================================
# SAVE STILL-FAILED DATES
# ============================================================

if still_failed:

    print("DATES STILL FAILED:")
    print("-" * 40)

    for date in still_failed:
        print(date)

    retry_file = "data/weather/failed_imerg_dates_retry2.txt"

    with open(retry_file, "w", encoding="utf-8") as file:

        for date in still_failed:
            file.write(date + "\n")

    print()
    print(f"Still-failed dates saved to:")
    print(retry_file)

else:

    print("ALL 44 FAILED DATES WERE SUCCESSFULLY RECOVERED.")


print("=" * 60)