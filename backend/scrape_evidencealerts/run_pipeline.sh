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
# --- New Step Configuration ---
SUBDISCIPLINE_SCRIPT="../subdisciplines/gemini.py" # Path as provided by user

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
echo "[Step 1/4] Running Scraper: ${SCRAPER_SCRIPT}" # Updated step count
python3 "${SCRAPER_SCRIPT}"
echo "[Step 1/4] Scraper finished."
echo

# 2. Check if scraper output exists and run the Summary Generator
echo "[Step 2/4] Checking for scraped data file: ${DATA_FILE}" # Updated step count

if [ -f "${DATA_FILE}" ]; then
    echo "[Step 2/4] Data file found. Running Summary Generator: ${GENERATOR_SCRIPT}"
    # Pass the path to the generated data.json file as an argument
    python3 "${GENERATOR_SCRIPT}" "${DATA_FILE}"
    echo "[Step 2/4] Summary Generator finished."
else
    echo "[Step 2/4] Warning: Scraped data file ${DATA_FILE} not found."
    echo "[Step 2/4] This might be okay if no new articles were found."
    echo "[Step 2/4] Skipping remaining steps for today." # Updated message
    # Exit gracefully if no data was scraped to summarize/export
    echo "========================================"
    echo "Pipeline finished (no new data)."
    echo "========================================"
    exit 0
fi
echo

# 3. Check if summaries directory exists and run the DB Exporter
echo "[Step 3/4] Checking for summaries directory: ${SUMMARIES_DIR}" # Updated step count

if [ -d "${SUMMARIES_DIR}" ]; then
    echo "[Step 3/4] Summaries directory found. Running Database Exporter: ${EXPORTER_SCRIPT}"
    # Pass the path to the directory containing summary JSON files
    python3 "${EXPORTER_SCRIPT}" "${SUMMARIES_DIR}"
    echo "[Step 3/4] Database Exporter finished."
else
    echo "[Step 3/4] Warning: Summaries directory ${SUMMARIES_DIR} not found or wasn't created."
    echo "[Step 3/4] Skipping Database Export and Subdiscipline steps." # Updated message
    # Exit gracefully if summaries dir doesn't exist, as Step 4 likely depends on it too
    echo "========================================"
    echo "Pipeline finished (Summaries directory missing)."
    echo "========================================"
    exit 0 # Changed from just skipping to exiting, assuming Step 4 needs summaries
fi
echo

# --- New Step 4: Run Subdiscipline Script ---
echo "[Step 4/4] Running Subdiscipline Script: ${SUBDISCIPLINE_SCRIPT}" # New step

# Assuming this script also depends on the summaries being generated.
# If it depends on something else (e.g., only the data.json), adjust the condition.
if [ -d "${SUMMARIES_DIR}" ]; then # Re-use the check, though technically redundant due to logic in Step 3 now
    echo "[Step 4/4] Summaries directory confirmed. Executing ${SUBDISCIPLINE_SCRIPT}..."
    # --- Execute the new script ---
    # Does it need arguments? Assuming it might need the summaries directory like the exporter. Adjust if not.
    python3 "${SUBDISCIPLINE_SCRIPT}"
    echo "[Step 4/4] Subdiscipline Script finished."
else
    # This case should ideally not be reached because of the exit 0 in Step 3's else block
    echo "[Step 4/4] Warning: Summaries directory ${SUMMARIES_DIR} not found. Skipping Subdiscipline Script."
fi
echo
# --- End of New Step 4 ---


echo "========================================"
echo "Pipeline finished successfully!"
echo "========================================"

exit 0