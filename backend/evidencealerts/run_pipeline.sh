#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipelines return the exit status of the last command to exit with non-zero status,
# or zero if all commands exit successfully.
set -o pipefail

# --- Virtual Environment Setup ---
echo "========================================"
echo "Setting up Python virtual environment..."
echo "========================================"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Virtual environment setup complete."
echo

# --- Configuration ---
SCRAPER_SCRIPT="scrape_evidence/scrape_evidencealerts.py"
GENERATOR_SCRIPT="scrape_evidence/generate_summaries.py"
EXPORTER_SCRIPT="scrape_evidence/export_to_db.py"
CLASSIFICATION_SCRIPT="classification_articles/reclassify_articles.py"
GRADING_SCRIPT="grade_articles/pubmed_grading.py"

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
echo "[Step 1/5] Running Scraper: ${SCRAPER_SCRIPT}"
python3 "${SCRAPER_SCRIPT}"
echo "[Step 1/5] Scraper finished."
echo

# 2. Check if scraper output exists and run the Summary Generator
echo "[Step 2/5] Checking for scraped data file: ${DATA_FILE}"

if [ -f "${DATA_FILE}" ]; then
    echo "[Step 2/5] Data file found. Running Summary Generator: ${GENERATOR_SCRIPT}"
    # Pass the path to the generated data.json file as an argument
    python3 "${GENERATOR_SCRIPT}" "${DATA_FILE}"
    echo "[Step 2/5] Summary Generator finished."
else
    echo "[Step 2/5] Warning: Scraped data file ${DATA_FILE} not found."
    echo "[Step 2/5] This might be okay if no new articles were found."
    echo "[Step 2/5] Summary Generator will be skipped."
fi
echo

# 3. Check if summaries directory exists and run the DB Exporter
echo "[Step 3/5] Checking for summaries directory: ${SUMMARIES_DIR}"

if [ -d "${SUMMARIES_DIR}" ]; then
    echo "[Step 3/5] Summaries directory found. Running Database Exporter: ${EXPORTER_SCRIPT}"
    # Pass the path to the directory containing summary JSON files
    python3 "${EXPORTER_SCRIPT}" "${SUMMARIES_DIR}"
    echo "[Step 3/5] Database Exporter finished."
else
    echo "[Step 3/5] Warning: Summaries directory ${SUMMARIES_DIR} not found or wasn't created."
    echo "[Step 3/5] Database Exporter will be skipped."
fi
echo

# 4. Run Article Classification
echo "[Step 4/5] Running Article Classification: ${CLASSIFICATION_SCRIPT}"
if [ -d "${SUMMARIES_DIR}" ]; then
    echo "[Step 4/5] Running classification script..."
    python3 "${CLASSIFICATION_SCRIPT}"
    echo "[Step 4/5] Article Classification finished."
else
    echo "[Step 4/5] Warning: Summaries directory ${SUMMARIES_DIR} not found. Skipping classification."
fi
echo

# 5. Run Article Grading
echo "[Step 5/5] Running Article Grading: ${GRADING_SCRIPT}"
if [ -d "${SUMMARIES_DIR}" ]; then
    echo "[Step 5/5] Running grading script..."
    python3 "${GRADING_SCRIPT}"
    echo "[Step 5/5] Article Grading finished."
else
    echo "[Step 5/5] Warning: Summaries directory ${SUMMARIES_DIR} not found. Skipping grading."
fi
echo

# Cleanup temporary directories
echo "========================================"
echo "Cleaning up temporary directories..."
echo "========================================"

echo "Removing temporary directories: data, links, summaries, result_arbitration"
rm -rf data links summaries result_arbitration
echo "Cleanup completed."

echo "========================================"
echo "Pipeline finished successfully!"
echo "========================================"

exit 0