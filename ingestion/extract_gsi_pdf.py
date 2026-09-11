from pathlib import Path
import re
import csv
import pdfplumber


# ==========================================
# FILE PATHS
# ==========================================

PDF_PATH = Path("data/raw/gsi/landslide_report.pdf")

OUTPUT_PATH = Path(
    "data/processed/gsi_inventory_raw.csv"
)


# ==========================================
# CHECK PDF
# ==========================================

if not PDF_PATH.exists():

    print("ERROR: PDF not found!")
    print(PDF_PATH)
    exit()


# ==========================================
# CREATE OUTPUT FOLDER
# ==========================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# CLEAN TEXT
# ==========================================

def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ==========================================
# DETECT NEW LANDSLIDE RECORD
# ==========================================

def is_record_start(line):

    return bool(
        re.match(
            r"^\s*\d+\s+\S+",
            line
        )
    )


# ==========================================
# EXTRACT COORDINATES
# ==========================================

def extract_coordinates(text):

    pattern = (
        r"(-?\d{1,2}\.\d{4,})"
        r"\s+"
        r"(-?\d{2,3}\.\d{4,})"
    )

    match = re.search(
        pattern,
        text
    )

    if not match:
        return None, None

    lat = float(match.group(1))
    lon = float(match.group(2))

    # India coordinate validation

    if not (
        6 <= lat <= 38
        and
        68 <= lon <= 98
    ):
        return None, None

    return lat, lon


# ==========================================
# START EXTRACTION
# ==========================================

print()
print("==========================================")
print("GSI LANDSLIDE INVENTORY EXTRACTION")
print("==========================================")
print()

print("PDF:")
print(PDF_PATH)

print()

print("Output:")
print(OUTPUT_PATH)

print()


# ==========================================
# OPEN CSV
# ==========================================

with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as csv_file:

    writer = csv.writer(csv_file)

    writer.writerow([
        "sl_no",
        "slide_no",
        "latitude",
        "longitude",
        "source_record"
    ])


    # ======================================
    # OPEN PDF
    # ======================================

    with pdfplumber.open(
        PDF_PATH
    ) as pdf:

        total_pages = len(pdf.pages)

        print(
            "Total pages:",
            total_pages
        )

        print()


        record_count = 0


        # ==================================
        # PROCESS ONE PAGE AT A TIME
        # ==================================

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            try:

                text = page.extract_text()

            except MemoryError:

                print(
                    f"MemoryError on page "
                    f"{page_number}"
                )

                continue

            if not text:
                continue


            lines = text.splitlines()

            current_record = []


            # ==============================
            # PROCESS LINES
            # ==============================

            for line in lines:

                line = clean_text(line)

                if not line:
                    continue


                # Ignore table headers

                if (
                    "Sl.No." in line
                    and
                    "Slide_No" in line
                ):
                    continue


                # ==========================
                # NEW RECORD
                # ==========================

                if is_record_start(line):

                    # Process previous record

                    if current_record:

                        record_text = " ".join(
                            current_record
                        )

                        # Serial + slide number

                        match = re.match(
                            r"^\s*(\d+)\s+(\S+)",
                            current_record[0]
                        )

                        if match:

                            sl_no = match.group(1)

                            slide_no = match.group(2)

                            lat, lon = (
                                extract_coordinates(
                                    record_text
                                )
                            )

                            if (
                                lat is not None
                                and
                                lon is not None
                            ):

                                writer.writerow([
                                    sl_no,
                                    slide_no,
                                    lat,
                                    lon,
                                    record_text
                                ])

                                record_count += 1


                    # Start new record

                    current_record = [line]


                else:

                    if current_record:

                        current_record.append(line)


            # ==============================
            # PROCESS LAST RECORD OF PAGE
            # ==============================

            if current_record:

                record_text = " ".join(
                    current_record
                )

                match = re.match(
                    r"^\s*(\d+)\s+(\S+)",
                    current_record[0]
                )

                if match:

                    sl_no = match.group(1)

                    slide_no = match.group(2)

                    lat, lon = (
                        extract_coordinates(
                            record_text
                        )
                    )

                    if (
                        lat is not None
                        and
                        lon is not None
                    ):

                        writer.writerow([
                            sl_no,
                            slide_no,
                            lat,
                            lon,
                            record_text
                        ])

                        record_count += 1


            # ==================================
            # PROGRESS
            # ==================================

            if (
                page_number % 20 == 0
                or
                page_number == total_pages
            ):

                print(
                    f"Processed "
                    f"{page_number}/{total_pages} "
                    f"pages | "
                    f"Records: {record_count}"
                )


            # ==================================
            # RELEASE PAGE MEMORY
            # ==================================

            page.flush_cache()


# ==========================================
# COMPLETE
# ==========================================

print()
print("==========================================")
print("EXTRACTION COMPLETE")
print("==========================================")

print()

print(
    "Total valid records:",
    record_count
)

print()

print(
    "CSV saved at:"
)

print(
    OUTPUT_PATH
)

print()

print("==========================================")