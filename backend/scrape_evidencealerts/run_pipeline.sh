#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipelines return the exit status of the last command to exit with non-zero status,
# or zero if all commands exit successfully.
set -o pipefail

# --- Configuration ---
SCRAPER_SCRIPT="scrape_evidencealerts.py"
GENERATOR_SCRIPT="generate_summaries.py"
EXPORTER_SCRIPT="export_to_db.py"

# Get today's date in YYYYMMDD format, consistent with Python scripts
TODAY_DATE=$(date +'%Y%m%d')

# Define expected output paths based on the Python scripts' logic
DATA_DIR="data/${TODAY_DATE}"
DATA_FILE="${DATA_DIR}/data.json"
SUMMARIES_DIR="summaries/${TODAY_DATE}"

# --- Execution ---

echo "========================================"
echo "Starting EvidenceAlerts Pipeline..."
echo "Date: ${TODAY_DATE}"
echo "========================================"
echo

# 1. Run the Scraper
echo "[Step 1/3] Running Scraper: ${SCRAPER_SCRIPT}"
python3 "${SCRAPER_SCRIPT}"
echo "[Step 1/3] Scraper finished."
echo

# 2. Check if scraper output exists and run the Summary Generator
echo "[Step 2/3] Checking for scraped data file: ${DATA_FILE}"

# Check if the data file was created by the scraper.
# Note: The scraper might run successfully but find no articles,
# in which case data.json might not be created or might be empty.
# generate_summaries.py should ideally handle a non-existent/empty input file.
if [ -f "${DATA_FILE}" ]; then
    echo "[Step 2/3] Data file found. Running Summary Generator: ${GENERATOR_SCRIPT}"
    # Pass the path to the generated data.json file as an argument
    python3 "${GENERATOR_SCRIPT}" "${DATA_FILE}"
    echo "[Step 2/3] Summary Generator finished."
else
    echo "[Step 2/3] Warning: Scraped data file ${DATA_FILE} not found."
    echo "[Step 2/3] This might be okay if no new articles were found."
    echo "[Step 2/3] Skipping Summary Generation and Database Export for today."
    # Exit gracefully if no data was scraped to summarize/export
    echo "========================================"
    echo "Pipeline finished (no new data)."
    echo "========================================"
    exit 0
fi
echo

# 3. Check if summaries directory exists and run the DB Exporter
echo "[Step 3/3] Checking for summaries directory: ${SUMMARIES_DIR}"

# Check if the summary generator created the output directory.
# Note: export_to_db.py should handle an empty directory gracefully.
if [ -d "${SUMMARIES_DIR}" ]; then
    echo "[Step 3/3] Summaries directory found. Running Database Exporter: ${EXPORTER_SCRIPT}"
    # Pass the path to the directory containing summary JSON files
    python3 "${EXPORTER_SCRIPT}" "${SUMMARIES_DIR}"
    echo "[Step 3/3] Database Exporter finished."
else
    # This case is less likely if Step 2 ran, as generate_summaries.py creates the dir.
    # Could happen if generate_summaries failed after creating the dir but before saving files,
    # or if it skipped all articles for some reason.
    echo "[Step 3/3] Warning: Summaries directory ${SUMMARIES_DIR} not found or wasn't created."
    echo "[Step 3/3] Skipping Database Export step."
fi
echo

echo "========================================"
echo "Pipeline finished successfully!"
echo "========================================"

exit 0