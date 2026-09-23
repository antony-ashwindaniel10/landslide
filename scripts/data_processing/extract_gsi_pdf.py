import os
from pypdf import PdfReader


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

PDF_FILE = "data/historical/GSI_landslide_inventory.pdf"
OUTPUT_FILE = "data/historical/GSI_landslide_inventory.txt"


# ---------------------------------------------------------
# Check PDF
# ---------------------------------------------------------

if not os.path.exists(PDF_FILE):
    print("ERROR: PDF file not found.")
    print(f"Expected location: {PDF_FILE}")
    raise SystemExit


# ---------------------------------------------------------
# Open PDF
# ---------------------------------------------------------

print("Opening GSI landslide inventory PDF...")

reader = PdfReader(PDF_FILE)

total_pages = len(reader.pages)

print(f"Total pages: {total_pages}")
print()


# ---------------------------------------------------------
# Extract text
# ---------------------------------------------------------

all_text = []

for page_number, page in enumerate(reader.pages, start=1):

    print(
        f"Extracting page {page_number}/{total_pages}",
        end="\r"
    )

    text = page.extract_text()

    if text:
        all_text.append(text)


# ---------------------------------------------------------
# Combine text
# ---------------------------------------------------------

full_text = "\n".join(all_text)


# ---------------------------------------------------------
# Save text
# ---------------------------------------------------------

os.makedirs(
    "data/historical",
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(full_text)


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print()
print()
print("PDF text extraction completed successfully.")
print(f"Pages processed: {total_pages}")
print(f"Characters extracted: {len(full_text):,}")
print(f"Saved to: {OUTPUT_FILE}")