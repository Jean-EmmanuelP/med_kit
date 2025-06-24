# Overall Workflow (`run_pipeline.sh`)

The `run_pipeline.sh` script is the master orchestrator for the entire data processing workflow. It is designed to be run on a recurring basis (e.g., daily) and manages the execution from start to finish.

[**← Back to Main Index**](../pipeline.md)

## Key Responsibilities

1.  **Environment Setup**:
    *   Automatically creates a Python virtual environment (`.venv`) if it doesn't already exist.
    *   Activates the virtual environment.
    *   Installs or updates all required Python packages from `requirements.txt`.

2.  **Sequential Execution**:
    *   Runs the five core Python scripts in a specific, logical order.
    *   The pipeline is designed to be fault-tolerant; for example, it checks if the scraper's output file exists before attempting to run the summarizer. If the file is missing, the step is skipped with a warning, allowing the pipeline to continue.

3.  **Cleanup**:
    *   After all steps are attempted, it executes a final cleanup command: `rm -rf data links summaries result_arbitration`.
    *   This removes all temporary directories and their contents, ensuring that the environment is clean for the next pipeline run and preventing the accumulation of old data.

## Script Configuration

The script uses `set -e -u -o pipefail` for robustness, ensuring that it exits immediately on any error, treats unset variables as an error, and correctly handles failures within command pipelines.